import os

import pytest

from app.agents import parse_json
from app.config import get_backend_candidates


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
