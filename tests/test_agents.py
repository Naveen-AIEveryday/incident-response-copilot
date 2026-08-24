import os

import pytest

from app.agents import (
    build_agent_telemetry,
    parse_and_validate,
    parse_json,
)
from app.config import get_backend_candidates
from app.models import (
    LogAnalysisOutput,
    RootCauseOutput,
    SeverityLevel,
    ShortRunbookOutput,
    TriageOutput,
)


class DummyResponse:
    def __init__(self, text):
        self.text = text


def test_parse_json_accepts_explanatory_text_and_trailing_commas():
    response = DummyResponse(
        '''
        Here is the root cause:
        {
          "root_cause": "Python was not added to the PATH environment variable.",
          "confidence": 70,
          "evidence": [
            "python is installed but vs code cannot find it"
          ],
          "recommended_remediation": "Add the Python installation directory to User PATH",
          "requires_human_approval": true,
        }
        '''
    )

    result = parse_json(response, "Root Cause Agent")

    assert result["root_cause"] == "Python was not added to the PATH environment variable."
    assert result["confidence"] == 70
    assert result["requires_human_approval"] is True


def test_parse_and_validate_root_cause_with_commands():
    response = DummyResponse(
        '''
        ```json
        {
          "root_cause": "Database connection pool exhaustion",
          "confidence": 85,
          "evidence": ["Connection pool exhausted (50/50)", "HTTP 500 error spike"],
          "recommended_remediation": "Increase max_connections to 100 after approval",
          "suggested_commands": ["netstat -tuln", "pg_isready -h localhost"],
          "requires_human_approval": true
        }
        ```
        '''
    )

    result = parse_and_validate(response, RootCauseOutput, "Root Cause Agent")
    assert result["confidence"] == 85
    assert len(result["suggested_commands"]) == 2
    assert "pg_isready -h localhost" in result["suggested_commands"]


def test_parse_and_validate_triage_severity():
    response = DummyResponse(
        '''
        {
          "severity": "critical",
          "affected_service": "payment-gateway",
          "incident_summary": "Payment checkout is failing completely.",
          "initial_investigation_steps": ["Check database", "Review recent releases"]
        }
        '''
    )

    result = parse_and_validate(response, TriageOutput, "Triage Agent")
    assert result["severity"] == SeverityLevel.CRITICAL
    assert result["affected_service"] == "payment-gateway"


def test_parse_and_validate_fallback_on_corrupt_response():
    response = DummyResponse('INVALID NON JSON RESPONSE')

    fallback = {
        "title": "Fallback Runbook",
        "summary": "Default recovery steps.",
        "steps": ["Step 1", "Step 2"],
    }

    result = parse_and_validate(
        response,
        ShortRunbookOutput,
        "Runbook Agent",
        fallback_defaults=fallback,
    )

    assert result["title"] == "Fallback Runbook"
    assert len(result["steps"]) == 2


def test_parse_json_rejects_non_object():
    response = DummyResponse('[]')

    with pytest.raises(ValueError, match="did not return a JSON object"):
        parse_json(response, "Root Cause Agent")


def test_generate_short_runbook_from_incident_and_kb():
    incident = {
        "title": "Website is not loading in Chrome",
        "description": "The website does not load in Google Chrome.",
        "logs": "ERR_CONNECTION_TIMED_OUT\nDNS_PROBE_FINISHED_NXDOMAIN",
    }
    knowledge = [
        {
            "title": "Chrome Website Loading Runbook",
            "content": "Check DNS resolution, verify network connectivity, and clear browser cache before escalating.",
        }
    ]

    runbook = parse_json(
        DummyResponse(
            '{"title": "Chrome Website Loading Runbook", "summary": "Check DNS and browser connectivity before escalating.", "steps": ["Verify DNS resolution", "Check network connectivity", "Clear Chrome cache"]}'
        ),
        "Runbook Agent",
    )

    assert runbook["title"] == "Chrome Website Loading Runbook"
    assert "dns" in runbook["summary"].lower()
    assert len(runbook["steps"]) >= 3


def test_build_agent_telemetry_tracks_latency_and_context_usage():
    telemetry = build_agent_telemetry(
        started_at=100.0,
        first_chunk_at=101.5,
        completed_at=104.2,
        prompt="incident details and investigation context",
        response_text="root cause summary",
        model="llama3.2",
        provider="cloud",
        context_window=128000,
    )

    assert telemetry["ttft_ms"] == 1500
    assert telemetry["total_ms"] == 4200
    assert telemetry["model"] == "llama3.2"
    assert telemetry["provider"] == "cloud"
    assert telemetry["context_usage_percent"] >= 0


def test_build_agent_telemetry_estimates_ttft_below_total_when_not_streaming():
    telemetry = build_agent_telemetry(
        started_at=100.0,
        first_chunk_at=104.2,
        completed_at=104.2,
        prompt="incident details and investigation context",
        response_text="root cause summary",
        model="llama3.2",
        provider="cloud",
        context_window=128000,
    )

    assert telemetry["ttft_ms"] < telemetry["total_ms"]
    assert telemetry["ttft_ms"] >= 0
    assert telemetry["total_ms"] >= 0


def test_get_backend_candidates_prioritizes_running_port_and_common_fallbacks():
    original_api_url = os.environ.get("API_URL")
    original_api_host = os.environ.get("API_HOST")
    original_api_port = os.environ.get("API_PORT")

    try:
        os.environ["API_URL"] = "http://127.0.0.1:9000"
        os.environ["API_HOST"] = "127.0.0.1"
        os.environ["API_PORT"] = "9000"

        candidates = get_backend_candidates()

        assert candidates[0] == "http://127.0.0.1:9000"
        assert "http://127.0.0.1:8000" in candidates
        assert "http://127.0.0.1:9001" in candidates
    finally:
        if original_api_url is None:
            os.environ.pop("API_URL", None)
        else:
            os.environ["API_URL"] = original_api_url

        if original_api_host is None:
            os.environ.pop("API_HOST", None)
        else:
            os.environ["API_HOST"] = original_api_host

        if original_api_port is None:
            os.environ.pop("API_PORT", None)
        else:
            os.environ["API_PORT"] = original_api_port

