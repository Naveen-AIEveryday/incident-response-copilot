import traceback

from fastapi import APIRouter, HTTPException

from app.models import ApprovalRequest, IncidentRequest
from app.orchestrator import Orchestrator


def create_routes(
    orchestrator: Orchestrator,
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def home():
        return {
            "message": (
                "Incident Response Copilot is running."
            )
        }

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

    return router