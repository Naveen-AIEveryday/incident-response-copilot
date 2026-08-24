from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentRequest(BaseModel):
    title: str = Field(..., description="Short title describing the incident")
    description: str = Field(..., description="Detailed description of symptoms and impact")
    logs: str = Field(..., description="Raw error logs, stack traces, or terminal output")


class ApprovalRequest(BaseModel):
    incident_id: str
    approved_by: str
    approved: bool
    comment: str = ""


class RunbookDocument(BaseModel):
    id: str = ""
    title: str
    content: str
    document_type: str = "runbook"
    tags: list[str] = Field(default_factory=list)
    score: float | None = None


class RunbookCreateRequest(BaseModel):
    title: str
    content: str
    document_type: str = "runbook"
    tags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Strict Agent Output Schemas
# ---------------------------------------------------------------------------

class TriageOutput(BaseModel):
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="Incident severity level")
    affected_service: str = Field(default="Unknown Service", description="Identified service or subsystem")
    incident_summary: str = Field(default="", description="Concise summary of the incident")
    initial_investigation_steps: list[str] = Field(default_factory=list, description="Immediate triage steps")


class LogAnalysisOutput(BaseModel):
    key_errors: list[str] = Field(default_factory=list, description="Extracted error messages or exception types")
    patterns: list[str] = Field(default_factory=list, description="Recognized failure patterns or anomalies")
    suspected_components: list[str] = Field(default_factory=list, description="Suspected failing infrastructure or code modules")
    evidence: list[str] = Field(default_factory=list, description="Concrete quotes and log snippets supporting the diagnosis")


class ShortRunbookOutput(BaseModel):
    title: str = Field(default="Incident Runbook", description="Short title of the actionable runbook")
    summary: str = Field(default="", description="1-sentence objective summary")
    steps: list[str] = Field(default_factory=list, description="Up to 3 high-impact actionable steps")


class RootCauseOutput(BaseModel):
    root_cause: str = Field(default="Unknown root cause", description="Primary probable failure mechanism")
    confidence: int = Field(default=50, ge=0, le=100, description="Confidence score between 0 and 100")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence items")
    recommended_remediation: str = Field(default="", description="One safe, human-reviewed remediation recommendation")
    suggested_commands: list[str] = Field(
        default_factory=list,
        description="Safe, read-only diagnostic or verification CLI commands (e.g. status checks, log queries)"
    )
    requires_human_approval: bool = Field(default=True, description="Enforces human sign-off requirement")


class IncidentResult(BaseModel):
    incident_id: str
    status: str
    triage: dict[str, Any]
    log_analysis: dict[str, Any]
    knowledge_matches: list[dict[str, Any]]
    short_runbook: dict[str, Any]
    root_cause_analysis: dict[str, Any]
    suggested_commands: list[str] = Field(default_factory=list)
    remediation_note: str
    approval: dict[str, Any] | None = None