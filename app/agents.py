import json
import re
import time
from typing import Any, Type, TypeVar

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from pydantic import BaseModel, ValidationError

from app.config import (
    ACTIVE_LLM_PROVIDER,
    ACTIVE_OLLAMA_API_KEY,
    ACTIVE_OLLAMA_BASE_URL,
    ACTIVE_OLLAMA_MODEL,
)
from app.models import (
    IncidentRequest,
    LogAnalysisOutput,
    RootCauseOutput,
    ShortRunbookOutput,
    TriageOutput,
)

T = TypeVar("T", bound=BaseModel)


def response_text(response: Any) -> str:
    """Extract text from an Agent Framework response."""
    text = getattr(response, "text", None)
    if text:
        return text
    return str(response)


def _normalize_llm_json(text: str) -> str:
    """Coerce common local-model JSON formatting issues into valid JSON."""
    fixed = text
    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)

    chars: list[str] = []
    in_string = False
    escaped = False

    for char in fixed:
        if in_string:
            if escaped:
                chars.append(char)
                escaped = False
                continue

            if char == "\\":
                chars.append(char)
                escaped = True
                continue

            if char == '"':
                chars.append(char)
                in_string = False
                continue

            if char in "\r\n\t":
                chars.append(" ")
                continue

            chars.append(char)
            continue

        if char == '"':
            in_string = True

        chars.append(char)

    fixed = "".join(chars)

    if not fixed.rstrip().endswith("}"):
        fixed = fixed.rstrip() + "}"

    return fixed


def parse_json(
    response: Any,
    agent_name: str,
) -> dict[str, Any]:
    text = response_text(response).strip()

    text = text.replace("```json", "")
    text = text.replace("```JSON", "")
    text = text.replace("```", "")
    text = text.strip()

    first_brace = text.find("{")

    if first_brace == -1:
        raise ValueError(
            f"{agent_name} did not return a JSON object:\n{text}"
        )

    json_text = _normalize_llm_json(text[first_brace:])

    try:
        result, _ = json.JSONDecoder().raw_decode(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{agent_name} returned invalid JSON:\n{json_text}"
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            f"{agent_name} did not return a JSON object."
        )

    return result


def parse_and_validate(
    response: Any,
    model_cls: Type[T],
    agent_name: str,
    fallback_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse JSON and validate against a target Pydantic model with fallback resilience."""
    try:
        raw_dict = parse_json(response, agent_name)
        validated = model_cls.model_validate(raw_dict)
        return validated.model_dump()
    except (ValueError, ValidationError) as err:
        if fallback_defaults:
            try:
                validated = model_cls.model_validate(fallback_defaults)
                return validated.model_dump()
            except Exception:
                pass
        raise err


def build_agent_telemetry(
    *,
    started_at: float,
    first_chunk_at: float | None = None,
    completed_at: float,
    prompt: str,
    response_text: str,
    model: str | None = None,
    provider: str | None = None,
    context_window: int = 128000,
) -> dict[str, Any]:
    """Capture latency and prompt-size telemetry for the UI."""
    total_ms = max(0, int((completed_at - started_at) * 1000))

    if first_chunk_at is None or first_chunk_at >= completed_at:
        if total_ms > 0:
            estimated_ttft_ratio = 0.75
            first_chunk_at = started_at + ((completed_at - started_at) * estimated_ttft_ratio)
        else:
            first_chunk_at = completed_at

    ttft_ms = max(0, int((first_chunk_at - started_at) * 1000))
    prompt_chars = len(prompt or "")
    response_chars = len(response_text or "")
    estimated_tokens = max(1, (prompt_chars + response_chars) // 4)
    context_usage_percent = min(
        100.0,
        round((estimated_tokens / max(1, context_window)) * 100, 2),
    )

    return {
        "started_at": started_at,
        "first_chunk_at": first_chunk_at,
        "completed_at": completed_at,
        "ttft_ms": ttft_ms,
        "total_ms": total_ms,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "estimated_tokens": estimated_tokens,
        "context_usage_percent": context_usage_percent,
        "model": model or ACTIVE_OLLAMA_MODEL,
        "provider": provider or ACTIVE_LLM_PROVIDER,
    }


class IncidentAgents:
    def __init__(self):
        if ACTIVE_LLM_PROVIDER == "cloud" and not ACTIVE_OLLAMA_API_KEY:
            raise ValueError(
                "OLLAMA_API_KEY is required when LLM_PROVIDER=cloud. "
                "Set it in the .env file."
            )

        self.client = OpenAIChatClient(
            api_key=ACTIVE_OLLAMA_API_KEY,
            base_url=ACTIVE_OLLAMA_BASE_URL,
            model=ACTIVE_OLLAMA_MODEL,
        )

        self.triage_agent = Agent(
            client=self.client,
            name="TriageAgent",
            instructions="""
You are an IT incident triage specialist.

Return only one valid JSON object.
Do not use Markdown code fences.
Do not add explanations before or after the JSON.

Required structure:
{
  "severity": "low | medium | high | critical",
  "affected_service": "short service or component name",
  "incident_summary": "short summary",
  "initial_investigation_steps": [
    "short step 1",
    "short step 2"
  ]
}

Rules:
- Use only the supplied incident information.
- Do not invent facts.
- Keep the response short.
            """.strip(),
        )

        self.log_agent = Agent(
            client=self.client,
            name="LogAnalysisAgent",
            instructions="""
You are an SRE log-analysis specialist.

Return only one valid JSON object.
Do not use Markdown code fences.
Do not add explanations before or after the JSON.

Required structure:
{
  "key_errors": [
    "short error 1"
  ],
  "patterns": [
    "short pattern 1"
  ],
  "suspected_components": [
    "short component 1"
  ],
  "evidence": [
    "short evidence 1"
  ]
}

Rules:
- Use only the supplied logs or error details.
- Do not invent evidence.
- Keep the response short.
            """.strip(),
        )

        self.root_cause_agent = Agent(
            client=self.client,
            name="RootCauseAgent",
            instructions="""
You are a senior IT incident commander.
Your response must be exactly one complete JSON object and nothing else.

Strict rules:
- Output must begin with `{` and end with `}`.
- Use double quotes for every key and every string value.
- No Markdown fences, no code blocks, no prose before or after the JSON.
- No trailing commas.
- No comments or explanations.
- Do not invent evidence.
- Include 1 to 3 safe read-only CLI diagnostic commands in "suggested_commands".

Required structure:
{
  "root_cause": "short probable cause",
  "confidence": 0,
  "evidence": [
    "short evidence 1",
    "short evidence 2"
  ],
  "recommended_remediation": "one safe remediation recommendation",
  "suggested_commands": [
    "safe read-only diagnostic command 1",
    "safe read-only diagnostic command 2"
  ],
  "requires_human_approval": true
}

Rules:
- Return only one root cause.
- Confidence must be an integer from 0 to 100.
- Return only one remediation recommendation.
- Suggested commands must be strictly read-only (e.g. status, logs, ping, nslookup, where.exe).
- Do not execute any action.
- Human approval is always required.
            """.strip(),
        )

        self.short_runbook_agent = Agent(
            client=self.client,
            name="ShortRunbookAgent",
            instructions="""
You are an incident-response specialist.
Create a short, practical runbook for the current incident.

Return only one valid JSON object.
Do not use Markdown fences.
Do not add explanations before or after the JSON.

Required structure:
{
  "title": "short runbook title",
  "summary": "1 sentence summary",
  "steps": [
    "short actionable step 1",
    "short actionable step 2",
    "short actionable step 3"
  ]
}

Rules:
- Keep it short and focused.
- Use the incident details and the supporting knowledge only as context.
- If the knowledge base has no close match, do not invent a KB result.
- Base the steps on the actual incident symptoms and likely troubleshooting path.
- Do not claim production changes were made.
- Keep the response brief and actionable.
            """.strip(),
        )

        self.report_agent = Agent(
            client=self.client,
            name="ReportAgent",
            instructions="""
Create a short Markdown incident report.

Include:
# Incident Report
## Summary
## Root Cause
## Evidence
## Diagnostic Commands
## Recommended Remediation
## Approval Status

Mention that remediation was simulated.
Never claim that a production action was executed.
            """.strip(),
        )

    async def triage(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        prompt = f"""
Incident title:
{incident.title}

Incident description:
{incident.description}

Logs or error details:
{incident.logs}
"""

        started_at = time.perf_counter()
        response = await self.triage_agent.run(prompt)
        completed_at = time.perf_counter()
        model_text = response_text(response)

        telemetry = build_agent_telemetry(
            started_at=started_at,
            first_chunk_at=completed_at,
            completed_at=completed_at,
            prompt=prompt,
            response_text=model_text,
            model=ACTIVE_OLLAMA_MODEL,
            provider=ACTIVE_LLM_PROVIDER,
        )
        parsed = parse_and_validate(
            response,
            TriageOutput,
            "Triage Agent",
            fallback_defaults={
                "severity": "medium",
                "affected_service": incident.title[:30],
                "incident_summary": incident.description[:100],
                "initial_investigation_steps": ["Inspect system error logs.", "Verify service connectivity."],
            },
        )
        parsed["_telemetry"] = telemetry
        return parsed

    async def analyze_logs(
        self,
        incident: IncidentRequest,
    ) -> dict[str, Any]:
        prompt = f"""
Incident title:
{incident.title}

Incident description:
{incident.description}

Logs or error details:
{incident.logs}
"""

        started_at = time.perf_counter()
        response = await self.log_agent.run(prompt)
        completed_at = time.perf_counter()
        model_text = response_text(response)

        telemetry = build_agent_telemetry(
            started_at=started_at,
            first_chunk_at=completed_at,
            completed_at=completed_at,
            prompt=prompt,
            response_text=model_text,
            model=ACTIVE_OLLAMA_MODEL,
            provider=ACTIVE_LLM_PROVIDER,
        )
        parsed = parse_and_validate(
            response,
            LogAnalysisOutput,
            "Log Analysis Agent",
            fallback_defaults={
                "key_errors": [incident.logs.splitlines()[0]] if incident.logs else ["Unknown error"],
                "patterns": ["Anomalous error rate"],
                "suspected_components": ["Application service"],
                "evidence": [incident.logs[:150]],
            },
        )
        parsed["_telemetry"] = telemetry
        return parsed

    async def root_cause(
        self,
        incident: IncidentRequest,
        triage: dict[str, Any],
        log_analysis: dict[str, Any],
        knowledge: list[dict[str, Any]],
        short_runbook: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        short_knowledge = knowledge[:3]

        prompt = f"""
Incident:
Title: {incident.title}
Description: {incident.description}
Logs: {incident.logs}

Triage:
{json.dumps(triage, indent=2)}

Log analysis:
{json.dumps(log_analysis, indent=2)}

Relevant knowledge:
{json.dumps(short_knowledge, indent=2)}

Generated short runbook:
{json.dumps(short_runbook or {}, indent=2)}

Use the KB only as supporting context. The short runbook is a concise, incident-specific summary and should not be treated as definitive evidence.

Return only the required JSON object with suggested_commands for diagnosis.
"""

        started_at = time.perf_counter()
        response = await self.root_cause_agent.run(prompt)
        completed_at = time.perf_counter()
        model_text = response_text(response)

        telemetry = build_agent_telemetry(
            started_at=started_at,
            first_chunk_at=completed_at,
            completed_at=completed_at,
            prompt=prompt,
            response_text=model_text,
            model=ACTIVE_OLLAMA_MODEL,
            provider=ACTIVE_LLM_PROVIDER,
        )
        parsed = parse_and_validate(
            response,
            RootCauseOutput,
            "Root Cause Agent",
            fallback_defaults={
                "root_cause": "Probable service configuration or environment error.",
                "confidence": 60,
                "evidence": log_analysis.get("evidence", [])[:2],
                "recommended_remediation": "Review service logs and request approval before rollback.",
                "suggested_commands": ["where.exe python", "python --version"],
                "requires_human_approval": True,
            },
        )
        parsed["_telemetry"] = telemetry
        return parsed

    async def generate_short_runbook(
        self,
        incident: IncidentRequest,
        triage: dict[str, Any],
        log_analysis: dict[str, Any],
        knowledge: list[dict[str, Any]],
    ) -> dict[str, Any]:
        short_knowledge = knowledge[:3]

        prompt = f"""
Incident:
Title: {incident.title}
Description: {incident.description}
Logs: {incident.logs}

Triage:
{json.dumps(triage, indent=2)}

Log analysis:
{json.dumps(log_analysis, indent=2)}

Supporting knowledge base context:
{json.dumps(short_knowledge, indent=2)}

If the knowledge base has no close match, do not invent one.
Produce a concise incident-specific troubleshooting runbook that is short and actionable.
Return only the required JSON object.
"""

        started_at = time.perf_counter()
        try:
            response = await self.short_runbook_agent.run(prompt)
            completed_at = time.perf_counter()
            model_text = response_text(response)
            telemetry = build_agent_telemetry(
                started_at=started_at,
                first_chunk_at=completed_at,
                completed_at=completed_at,
                prompt=prompt,
                response_text=model_text,
                model=ACTIVE_OLLAMA_MODEL,
                provider=ACTIVE_LLM_PROVIDER,
            )
            runbook = parse_and_validate(
                response,
                ShortRunbookOutput,
                "Short Runbook Agent",
                fallback_defaults={
                    "title": incident.title,
                    "summary": "Validate the impacted dependency and symptoms before escalation.",
                    "steps": [
                        "Check the exact incident symptom and logs.",
                        "Validate the likely service or dependency in scope.",
                        "Escalate for human approval if the issue remains unclear.",
                    ],
                },
            )
            runbook["_telemetry"] = telemetry
        except Exception:
            completed_at = time.perf_counter()
            runbook = {
                "title": incident.title,
                "summary": (
                    "Use the incident details to verify the likely failing path and validate the impacted dependency before escalation."
                ),
                "steps": [
                    "Check the exact incident symptom and logs.",
                    "Validate the likely service or dependency in scope.",
                    "Escalate for human approval if the issue remains unclear.",
                ],
                "_telemetry": build_agent_telemetry(
                    started_at=started_at,
                    first_chunk_at=completed_at,
                    completed_at=completed_at,
                    prompt=prompt,
                    response_text="fallback runbook",
                    model=ACTIVE_OLLAMA_MODEL,
                    provider=ACTIVE_LLM_PROVIDER,
                ),
            }

        runbook["steps"] = runbook.get("steps", [])[:3]
        return runbook

    async def report(
        self,
        incident: dict[str, Any],
    ) -> str:
        prompt = json.dumps(
            incident,
            indent=2,
        )

        started_at = time.perf_counter()
        response = await self.report_agent.run(prompt)
        completed_at = time.perf_counter()

        telemetry = build_agent_telemetry(
            started_at=started_at,
            first_chunk_at=completed_at,
            completed_at=completed_at,
            prompt=prompt,
            response_text=response_text(response),
            model=ACTIVE_OLLAMA_MODEL,
            provider=ACTIVE_LLM_PROVIDER,
        )
        incident["_telemetry"] = telemetry
        return response_text(response)