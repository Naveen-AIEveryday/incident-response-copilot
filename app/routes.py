from fastapi import APIRouter, HTTPException

from app.models import (
    ApprovalRequest,
    DocumentRequest,
    IncidentRequest,
)
from app.orchestrator import IncidentOrchestrator


def create_router(orchestrator: IncidentOrchestrator):
    router = APIRouter()

    @router.get("/")
    async def home():
        return {
            "message": "Incident Response Copilot is running.",
            "hitl_ui": "Run Streamlit separately with: streamlit run ui/streamlit_app.py",
        }

    @router.post("/documents")
    async def add_document(request: DocumentRequest):
        document_id = orchestrator.knowledge_base.add_document(
            title=request.title,
            content=request.content,
            document_type=request.document_type,
        )

        return {
            "message": "Document added.",
            "document_id": document_id,
        }

    @router.post("/incidents")
    async def create_incident(request: IncidentRequest):
        return await orchestrator.investigate(request)

    @router.get("/incidents/{incident_id}")
    async def get_incident(incident_id: str):
        incident = orchestrator.database.get_incident(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident was not found.",
            )

        return incident

    @router.get("/incidents/{incident_id}/audit")
    async def get_audit(incident_id: str):
        incident = orchestrator.database.get_incident(incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident was not found.",
            )

        return {
            "incident_id": incident_id,
            "events": orchestrator.database.get_events(incident_id),
        }

    @router.post("/incidents/approval")
    async def approve_incident(request: ApprovalRequest):
        return await orchestrator.approve(request)

    @router.post("/incidents/{incident_id}/report")
    async def create_report(incident_id: str):
        return await orchestrator.report(incident_id)

    return router