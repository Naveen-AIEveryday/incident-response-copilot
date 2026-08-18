import asyncio
import json
import uuid
from typing import Any

from fastapi import HTTPException

from app.agents import IncidentAgents
from app.database import Database
from app.knowledge_base import KnowledgeBase
from app.models import ApprovalRequest, IncidentRequest
from app.plugins import create_kernel


class Orchestrator:
    def __init__(
        self,
        database: Database,
        knowledge_base: KnowledgeBase,
        agents: IncidentAgents,
    ):
        self.database = database
        self.knowledge_base = knowledge_base
        self.agents = agents

        # Semantic Kernel plugin used for knowledge retrieval.
        self.kernel, self.knowledge_plugin = create_kernel(
            knowledge_base
        )

    async def investigate(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        incident_id = str(uuid.uuid4())
        incident_data = incident.model_dump()

        self.database.create_incident(
            incident_id=incident_id,
            incident=incident_data,
        )

        self.database.add_event(
            incident_id,
            "incident_created",
            {
                "title": incident.title,
            },
        )

        # Triage and log analysis are independent, so they run together.
        triage, log_analysis = await asyncio.gather(
            self.agents.triage(incident),
            self.agents.analyze_logs(incident),
        )

        self.database.add_event(
            incident_id,
            "triage_completed",
            triage,
        )

        self.database.add_event(
            incident_id,
            "log_analysis_completed",
            log_analysis,
        )

        # Send complete incident context to the knowledge search.
        search_query = f"""
Incident title:
{incident.title}

Incident description:
{incident.description}

Incident logs:
{incident.logs}

Triage result:
{json.dumps(triage, indent=2)}

Log-analysis result:
{json.dumps(log_analysis, indent=2)}
"""

        knowledge_json = (
            self.knowledge_plugin.search_knowledge(
                search_query
            )
        )

        # Keep KB context deliberately short and relevant.
        knowledge = json.loads(knowledge_json)[:1]

        self.database.add_event(
            incident_id,
            "knowledge_retrieval_completed",
            {
                "documents": knowledge,
            },
        )

        short_runbook = await self.agents.generate_short_runbook(
            incident=incident,
            triage=triage,
            log_analysis=log_analysis,
            knowledge=knowledge,
        )

        self.database.add_event(
            incident_id,
            "short_runbook_generated",
            short_runbook,
        )

        root_cause = await self.agents.root_cause(
            incident=incident,
            triage=triage,
            log_analysis=log_analysis,
            knowledge=knowledge,
            short_runbook=short_runbook,
        )

        self.database.add_event(
            incident_id,
            "root_cause_completed",
            root_cause,
        )

        result = {
            "incident_id": incident_id,
            "status": "pending_human_approval",
            "triage": triage,
            "log_analysis": log_analysis,
            "knowledge_matches": knowledge,
            "short_runbook": short_runbook,
            "root_cause_analysis": root_cause,
            "remediation_note": (
                "No production action was executed. "
                "Human approval is required."
            ),
        }

        self.database.update_incident(
            incident_id=incident_id,
            status="pending_human_approval",
            result=result,
        )

        return result

    async def approve(
        self,
        request: ApprovalRequest,
    ) -> dict[str, str]:
        incident = self.database.get_incident(
            request.incident_id
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found.",
            )

        if incident["status"] != "pending_human_approval":
            raise HTTPException(
                status_code=400,
                detail="Approval was already completed.",
            )

        if request.approved:
            status = "remediation_approved"
            message = (
                "Remediation approved. "
                "No production action was executed."
            )
        else:
            status = "remediation_rejected"
            message = (
                "Remediation rejected. "
                "No production action was executed."
            )

        result = incident["result"] or {}

        result["approval"] = {
            "approved": request.approved,
            "approved_by": request.approved_by,
            "comment": request.comment,
        }

        self.database.update_incident(
            incident_id=request.incident_id,
            status=status,
            result=result,
        )

        self.database.add_event(
            request.incident_id,
            "human_approval",
            result["approval"],
        )

        return {
            "incident_id": request.incident_id,
            "status": status,
            "message": message,
        }

    async def create_report(
        self,
        incident_id: str,
    ) -> dict[str, str]:
        incident = self.database.get_incident(
            incident_id
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found.",
            )

        if incident["status"] == "pending_human_approval":
            raise HTTPException(
                status_code=400,
                detail="Human approval is required first.",
            )

        report = await self.agents.report(incident)

        self.database.add_event(
            incident_id,
            "report_generated",
            {},
        )

        return {
            "incident_id": incident_id,
            "report": report,
        }