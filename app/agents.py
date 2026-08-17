import json
from typing import Any

from agent_framework import Agent
from agent_framework.ollama import OllamaChatClient
from app.config import OLLAMA_HOST, OLLAMA_MODEL

from app.models import IncidentRequest


def response_text(response: Any) -> str:
    """
    Extracts text from an Agent Framework response.
    """
    text = getattr(response, "text", None)

    if text:
        return text

    return str(response)


def parse_json_response(
    response: Any,
    agent_name: str,
) -> dict[str, Any]:
    text = response_text(response).strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json")
        text = text.removesuffix("```")
        text = text.strip()

    elif text.startswith("```"):
        text = text.removeprefix("```")
        text = text.removesuffix("```")
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{agent_name} returned invalid JSON: {text}"
        ) from error


class IncidentAgents:
    def __init__(self):
        self.client = OllamaChatClient(
            host=OLLAMA_HOST,
            model=OLLAMA_MODEL,
        )

        self.triage_agent = Agent(
            client=self.client,
            name="TriageAgent",
            instructions="""
You are an IT incident triage specialist.

Return valid JSON only. Do not use Markdown.

Required structure:
{
  "severity": "low | medium | high | critical",
  "affected_service": "service name",
  "incident_summary": "short summary",
  "initial_investigation_steps": [
    "step 1",
    "step 2",
    "step 3"
  ]
}

Use only the supplied incident information.
            """,
        )

        self.log_agent = Agent(
            client=self.client,
            name="LogAnalysisAgent",
            instructions="""
You are an SRE log analysis specialist.

Return valid JSON only. Do not use Markdown.

Required structure:
{
  "key_errors": ["error 1", "error 2"],
  "patterns": ["pattern 1", "pattern 2"],
  "suspected_components": ["component 1"],
  "evidence": ["evidence from supplied logs"]
}

Do not invent log entries.
            """,
        )

        self.root_cause_agent = Agent(
            client=self.client,
            name="RootCauseAgent",
            instructions="""
You are a senior incident commander.

Use the incident, triage, log analysis, and knowledge-base evidence.

Return valid JSON only. Do not use Markdown.

Required structure:
{
  "root_cause_hypotheses": [
    {
      "cause": "probable cause",
      "confidence": 0,
      "evidence": ["evidence 1", "evidence 2"]
    }
  ],
  "recommended_remediation": [
    "safe step 1",
    "safe step 2"
  ],
  "requires_human_approval": true
}

Rules:
- Return no more than three hypotheses.
- Confidence must be an integer between 0 and 100.
- Never claim that a remediation was executed.
- Human approval is always required.
            """,
        )

        self.report_agent = Agent(
            client=self.client,
            name="ReportAgent",
            instructions="""
Create a concise Markdown incident report.

Include:
# Incident Report
## Incident Summary
## Impact
## Evidence
## Root Cause Hypotheses
## Recommended Remediation
## Approval Status
## Prevention Recommendations

Never claim that a production action was executed.
            """,
        )

    async def triage(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        prompt = f"""
Title:
{incident.title}

Description:
{incident.description}

Logs:
{incident.logs}
"""

        response = await self.triage_agent.run(prompt)
        return parse_json_response(response, "Triage agent")

    async def analyze_logs(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        prompt = f"""
Title:
{incident.title}

Logs:
{incident.logs}
"""

        response = await self.log_agent.run(prompt)
        return parse_json_response(response, "Log analysis agent")

    async def analyze_root_cause(
        self,
        incident: IncidentRequest,
        triage: dict[str, Any],
        log_analysis: dict[str, Any],
        knowledge_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = f"""
Incident:
{incident.model_dump_json(indent=2)}

Triage:
{json.dumps(triage, indent=2)}

Log analysis:
{json.dumps(log_analysis, indent=2)}

Knowledge-base evidence:
{json.dumps(knowledge_matches, indent=2)}
"""

        response = await self.root_cause_agent.run(prompt)
        return parse_json_response(response, "Root cause agent")

    async def create_report(
        self,
        incident: dict[str, Any],
        approval_status: str,
    ) -> str:
        prompt = f"""
Incident details:
{json.dumps(incident, indent=2)}

Approval status:
{approval_status}
"""

        response = await self.report_agent.run(prompt)
        return response_text(response)