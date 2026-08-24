import asyncio
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents import IncidentAgents
from app.database import Database
from app.knowledge_base import KnowledgeBase
from app.models import ApprovalRequest, IncidentRequest
from app.orchestrator import Orchestrator


DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(DATA_DIR / "incidents.db")

# Create a single-process runtime that preserves the current incident workflow
# but avoids the local two-service FastAPI + Streamlit startup model.
database = Database(DB_PATH)
knowledge_base = KnowledgeBase()
agents = IncidentAgents()
orchestrator = Orchestrator(
    database=database,
    knowledge_base=knowledge_base,
    agents=agents,
)


st.set_page_config(
    page_title="Incident Response Copilot",
    layout="wide",
)

st.title("Agentic IT Incident Response Copilot")
st.caption("AI-assisted incident investigation with human approval.")

if "incident_result" not in st.session_state:
    st.session_state.incident_result = None
if "approval_result" not in st.session_state:
    st.session_state.approval_result = None
if "report_result" not in st.session_state:
    st.session_state.report_result = None


def run_investigation(title: str, description: str, logs: str):
    request = IncidentRequest(
        title=title,
        description=description,
        logs=logs,
    )
    return asyncio.run(orchestrator.investigate(request))


def run_approval(incident_id: str, approved: bool, engineer: str, comment: str):
    request = ApprovalRequest(
        incident_id=incident_id,
        approved_by=engineer,
        approved=approved,
        comment=comment,
    )
    return asyncio.run(orchestrator.approve(request))


def run_report(incident_id: str):
    return asyncio.run(orchestrator.create_report(incident_id))


def render_summary_table(rows: list[dict[str, str]]) -> None:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


with st.form("incident_form"):
    st.subheader("Submit an incident")
    title = st.text_input(
        "Incident title",
        value="Python is not recognized in VS Code",
    )
    description = st.text_area(
        "Incident description",
        value=(
            "Python is installed, but the Python command "
            "is not working in the VS Code terminal."
        ),
        height=100,
    )
    logs = st.text_area(
        "Logs or error details",
        value=(
            "'python' is not recognized as an internal or external command.\n"
            "Python is installed, but VS Code cannot identify the Python interpreter."
        ),
        height=160,
    )
    investigate_clicked = st.form_submit_button("Investigate incident", type="primary")

if investigate_clicked:
    status = st.empty()
    status.info(
        "Investigating the incident... this can take a minute while the agents analyze logs and knowledge base context."
    )
    try:
        result = run_investigation(title=title, description=description, logs=logs)
    finally:
        status.empty()

    if result:
        st.session_state.incident_result = result
        st.session_state.approval_result = None
        st.session_state.report_result = None
        st.success("Investigation completed.")
        st.rerun()

result = st.session_state.incident_result
if result:
    st.divider()
    st.subheader("Investigation result")
    incident_id = result.get("incident_id", "")
    status_value = result.get("status", "")
    st.write(f"**Incident ID:** `{incident_id}`")
    st.write(f"**Status:** `{status_value}`")

    triage = result.get("triage", {})
    log_analysis = result.get("log_analysis", {})
    root_cause = result.get("root_cause_analysis", {})

    investigation_rows = [
        {"Field": "Severity", "Value": str(triage.get("severity", ""))},
        {"Field": "Affected Service", "Value": str(triage.get("affected_service", ""))},
        {"Field": "Summary", "Value": str(triage.get("incident_summary", ""))},
        {"Field": "KB Matches", "Value": str(len(result.get("knowledge_matches", [])))},
    ]
    render_summary_table(investigation_rows)

    with st.expander("Triage"):
        st.json(triage)
    with st.expander("Log Analysis"):
        st.json(log_analysis)
    with st.expander("Knowledge Matches"):
        st.json(result.get("knowledge_matches", []))
    with st.expander("Short Runbook"):
        st.json(result.get("short_runbook", {}))
    with st.expander("Root Cause Analysis"):
        st.json(root_cause)

    suggested_commands = result.get("suggested_commands", []) or root_cause.get("suggested_commands", [])
    if suggested_commands:
        st.subheader("Recommended Safe Diagnostic Commands (Read-Only)")
        for cmd in suggested_commands:
            st.code(cmd, language="bash")


    approval_form = st.form(f"approval_form_{incident_id}")
    approval_form.subheader("Human approval")
    approved_by = approval_form.text_input(
        "Approving engineer email",
        value="unaveen0511@gmail.com",
    )
    approval_comment = approval_form.text_area("Approval comment", value="Approved for review.")
    approval_choice = approval_form.radio(
        "Decision",
        ["Approve", "Reject"],
        index=0,
    )
    approval_clicked = approval_form.form_submit_button("Submit approval")

    if approval_clicked:
        approval_response = run_approval(
            incident_id=incident_id,
            approved=(approval_choice == "Approve"),
            engineer=approved_by,
            comment=approval_comment,
        )
        st.session_state.approval_result = approval_response
        st.success(f"Approval submitted: {approval_response.get('status', '')}")
        st.rerun()

    report_clicked = st.button("Generate report", key=f"report_{incident_id}")
    if report_clicked:
        report_result = run_report(incident_id)
        st.session_state.report_result = report_result
        if report_result:
            st.success("Report generated.")
            st.markdown(report_result.get("report", ""))
            st.rerun()

approval_result = st.session_state.approval_result
if approval_result:
    st.divider()
    st.subheader("Approval outcome")
    st.json(approval_result)

report_result = st.session_state.report_result
if report_result:
    st.divider()
    st.subheader("Incident report")
    st.markdown(report_result.get("report", ""))
