import traceback

from fastapi import APIRouter, HTTPException, Query

from app.models import (
    ApprovalRequest,
    IncidentRequest,
    RunbookCreateRequest,
)
from app.orchestrator import Orchestrator


def create_routes(
    orchestrator: Orchestrator,
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def home():
        return {
            "message": "Incident Response Copilot is running.",
            "version": "2.0",
        }

    # -----------------------------------------------------------------------
    # Incidents API
    # -----------------------------------------------------------------------

    @router.get("/incidents")
    async def list_incidents(
        status: str | None = Query(None, description="Filter by incident status"),
        search: str | None = Query(None, description="Search term in title, description, or logs"),
        limit: int = Query(100, ge=1, le=500),
    ):
        return orchestrator.database.list_incidents(
            status=status,
            search_query=search,
            limit=limit,
        )

    @router.post("/incidents")
    async def investigate(
        request: IncidentRequest,
    ):
        try:
            return await orchestrator.investigate(
                request
            )
        except Exception as error:
            print("\n===== BACKEND ERROR =====")
            traceback.print_exc()
            print("=========================\n")

            raise HTTPException(
                status_code=500,
                detail=str(error),
            ) from error

    @router.post("/incidents/approval")
    async def approval(
        request: ApprovalRequest,
    ):
        return await orchestrator.approve(request)

    @router.post(
        "/incidents/{incident_id}/report"
    )
    async def report(
        incident_id: str,
    ):
        return await orchestrator.create_report(
            incident_id
        )

    @router.get(
        "/incidents/{incident_id}"
    )
    async def get_incident(
        incident_id: str,
    ):
        incident = orchestrator.database.get_incident(
            incident_id
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found.",
            )

        return incident

    @router.delete(
        "/incidents/{incident_id}"
    )
    async def delete_incident(
        incident_id: str,
    ):
        deleted = orchestrator.database.delete_incident(incident_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Incident not found.",
            )
        return {"incident_id": incident_id, "deleted": True}

    @router.get(
        "/incidents/{incident_id}/audit"
    )
    async def audit(
        incident_id: str,
    ):
        incident = orchestrator.database.get_incident(
            incident_id
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found.",
            )

        return {
            "incident_id": incident_id,
            "events": orchestrator.database.get_events(
                incident_id
            ),
        }

    # -----------------------------------------------------------------------
    # Knowledge Base / Runbooks API
    # -----------------------------------------------------------------------

    @router.get("/knowledge/runbooks")
    async def list_runbooks(
        document_type: str | None = Query(None, description="Filter by document type"),
    ):
        return orchestrator.list_runbooks(document_type=document_type)

    @router.post("/knowledge/runbooks")
    async def create_runbook(
        request: RunbookCreateRequest,
    ):
        return orchestrator.add_runbook(
            title=request.title,
            content=request.content,
            document_type=request.document_type,
            tags=request.tags,
        )

    @router.delete("/knowledge/runbooks/{runbook_id}")
    async def delete_runbook(
        runbook_id: str,
    ):
        deleted = orchestrator.delete_runbook(runbook_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Runbook not found.",
            )
        return {"runbook_id": runbook_id, "deleted": True}

    @router.get("/knowledge/search")
    async def search_knowledge(
        q: str = Query(..., description="Search query string"),
        limit: int = Query(5, ge=1, le=20),
    ):
        return orchestrator.search_runbooks(query=q, limit=limit)

    return router