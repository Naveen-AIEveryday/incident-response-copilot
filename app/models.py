from typing import Any

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    title: str
    description: str
    logs: str


class ApprovalRequest(BaseModel):
    incident_id: str
    approved_by: str
    approved: bool
    comment: str = ""


class DocumentRequest(BaseModel):
    title: str
    content: str
    document_type: str = "runbook"


class IncidentResult(BaseModel):
    incident_id: str
    status: str
    triage: dict[str, Any]
    log_analysis: dict[str, Any]
    knowledge_matches: list[dict[str, Any]]
    root_cause_analysis: dict[str, Any]
    remediation_note: str