import asyncio
import json
import uuid
from typing import Any

from fastapi import HTTPException

from app.agents import IncidentAgents
from app.database import AuditDatabase
from app.knowledge_base import KnowledgeBase
from app.models import ApprovalRequest, IncidentRequest
from app.plugins import KnowledgePlugin, create_kernel


class IncidentOrchestrator:
    def __init__(
        self,
        database: AuditDatabase,
        knowledge_base: KnowledgeBase,
        agents: IncidentAgents,
    ):
        self.database = database
        self.knowledge_base = knowledge_base
        self.agents = agents

        # Semantic Kernel is used for the knowledge plugin layer.
        self.kernel = create_kernel(knowledge_base)
        self.knowledge_plugin = KnowledgePlugin(knowledge_base)

    async def investigate(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        incident_id = str(uuid.uuid4())

        self.database.create_incident(
            incident_id=incident_id,
            title=incident.title,
            description=incident.description,
            logs=incident.logs,
        )

        self.database.add_event(
            incident_id,
            "incident_created",
            {"title": incident.title},
        )

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

        search_query = (
            f"{incident.title}\n"
            f"{incident.description}\n"
            f"{json.dumps(log_analysis)}"
        )

        # Semantic Kernel plugin function.
        knowledge_json = (
            self.knowledge_plugin.search_incident_knowledge(search_query)
        )

        knowledge_matches = json.loads(knowledge_json)

        self.database.add_event(
            incident_id,
            "knowledge_retrieval_completed",
            {"matches": knowledge_matches},
        )

        root_cause = await self.agents.analyze_root_cause(
            incident=incident,
            triage=triage,
            log_analysis=log_analysis,
            knowledge_matches=knowledge_matches,
        )

        self.database.add_event(
            incident_id,
            "root_cause_analysis_completed",
            root_cause,
        )

        result = {
            "incident_id": incident_id,
            "status": "pending_human_approval",
            "triage": triage,
            "log_analysis": log_analysis,
            "knowledge_matches": knowledge_matches,
            "root_cause_analysis": root_cause,
            "remediation_note": (
                "No remediation was executed. "
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
        approval: ApprovalRequest,
    ) -> dict[str, Any]:
        incident = self.database.get_incident(approval.incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident was not found.",
            )

        if incident["status"] != "pending_human_approval":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Incident is not waiting for approval. "
                    f"Current status: {incident['status']}"
                ),
            )

        if approval.approved:
            status = "remediation_approved"
            message = (
                "Remediation approved by the human reviewer. "
                "No production action was executed."
            )
        else:
            status = "remediation_rejected"
            message = (
                "Remediation rejected by the human reviewer. "
                "No production action was executed."
            )

        approval_details = {
            "approved": approval.approved,
            "approved_by": approval.approved_by,
            "comment": approval.comment,
            "message": message,
        }

        self.database.add_event(
            approval.incident_id,
            "human_approval",
            approval_details,
        )

        result = incident["result"] or {}
        result["approval"] = approval_details

        self.database.update_incident(
            incident_id=approval.incident_id,
            status=status,
            result=result,
        )

        return {
            "incident_id": approval.incident_id,
            "status": status,
            "message": message,
        }

    async def report(
        self,
        incident_id: str,
    ) -> dict[str, Any]:
        incident = self.database.get_incident(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident was not found.",
            )

        report = await self.agents.create_report(
            incident=incident,
            approval_status=incident["status"],
        )

        self.database.add_event(
            incident_id,
            "report_generated",
            {"generated": True},
        )

        return {
            "incident_id": incident_id,
            "status": incident["status"],
            "report": report,
        }