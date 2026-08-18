import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import API_URL


st.set_page_config(
    page_title="Incident Response Copilot",
    layout="wide",
)

st.title("Agentic IT Incident Response Copilot")
st.caption(
    "AI-assisted incident investigation with human approval."
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "incident_result" not in st.session_state:
    st.session_state.incident_result = None

if "approval_result" not in st.session_state:
    st.session_state.approval_result = None

if "report_result" not in st.session_state:
    st.session_state.report_result = None


# ---------------------------------------------------------
# Backend API functions
# ---------------------------------------------------------

def call_investigation(
    title: str,
    description: str,
    logs: str,
):
    try:
        response = requests.post(
            f"{API_URL}/incidents",
            json={
                "title": title,
                "description": description,
                "logs": logs,
            },
            timeout=180,
        )

        if response.status_code == 405:
            st.error(
                "The configured backend URL is wrong for this app. "
                f"Use the FastAPI API at {API_URL}, not the Streamlit port."
            )
            return None

        if response.status_code != 200:
            st.error(
                f"Backend error {response.status_code}: {response.text}"
            )
            return None

        return response.json()

    except requests.RequestException as error:
        st.error(
            f"Could not connect to the backend at {API_URL}: {error}"
        )
        return None


def call_approval(
    incident_id: str,
    approved: bool,
    engineer: str,
    comment: str,
):
    try:
        response = requests.post(
            f"{API_URL}/incidents/approval",
            json={
                "incident_id": incident_id,
                "approved": approved,
                "approved_by": engineer,
                "comment": comment,
            },
            timeout=60,
        )

        if response.status_code != 200:
            st.error(
                f"Approval error {response.status_code}: {response.text}"
            )
            return None

        return response.json()

    except requests.RequestException as error:
        st.error(
            f"Could not connect to the backend at {API_URL}: {error}"
        )
        return None


def call_report(
    incident_id: str,
):
    try:
        response = requests.post(
            f"{API_URL}/incidents/{incident_id}/report",
            timeout=180,
        )

        if response.status_code != 200:
            st.error(
                f"Report error {response.status_code}: {response.text}"
            )
            return None

        return response.json()

    except requests.RequestException as error:
        st.error(
            f"Could not connect to the backend at {API_URL}: {error}"
        )
        return None


def render_summary_table(rows: list[dict[str, str]]) -> None:
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# Incident form
# ---------------------------------------------------------

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
            "'python' is not recognized as an internal or "
            "external command.\n"
            "Python is installed, but VS Code cannot identify "
            "the Python interpreter."
        ),
        height=160,
    )

    investigate_clicked = st.form_submit_button(
        "Investigate incident",
        type="primary",
    )


if investigate_clicked:
    status = st.empty()
    status.info(
        "Investigating the incident... this can take a minute while the agents analyze logs and knowledge base context."
    )

    try:
        result = call_investigation(
            title=title,
            description=description,
            logs=logs,
        )
    finally:
        status.empty()

    if result:
        st.session_state.incident_result = result
        st.session_state.approval_result = None
        st.session_state.report_result = None

        st.success("Investigation completed.")
        st.rerun()


# ---------------------------------------------------------
# Investigation result
# ---------------------------------------------------------

result = st.session_state.incident_result

if result:
    st.divider()
    st.subheader("Investigation result")

    incident_id = result.get(
        "incident_id",
        "",
    )

    status = result.get(
        "status",
        "",
    )

    st.write(
        f"**Incident ID:** `{incident_id}`"
    )

    st.write(
        f"**Status:** `{status}`"
    )

    triage = result.get(
        "triage",
        {},
    )

    log_analysis = result.get(
        "log_analysis",
        {},
    )

    root_cause = result.get(
        "root_cause_analysis",
        {},
    )

    investigation_rows = [
        {
            "Field": "Severity",
            "Value": str(
                triage.get(
                    "severity",
                    "unknown",
                )
            ).upper(),
        },
        {
            "Field": "Affected service",
            "Value": triage.get(
                "affected_service",
                "unknown",
            ),
        },
        {
            "Field": "Confidence",
            "Value": f"{root_cause.get('confidence', 0)}%",
        },
        {
            "Field": "Incident summary",
            "Value": triage.get(
                "incident_summary",
                "No summary returned.",
            ),
        },
    ]

    st.subheader("Investigation summary")
    render_summary_table(investigation_rows)

    st.subheader("Incident summary")

    st.write(
        triage.get(
            "incident_summary",
            "No summary returned.",
        )
    )

    st.subheader("Initial investigation steps")

    investigation_steps = triage.get(
        "initial_investigation_steps",
        [],
    )

    if investigation_steps:
        for step in investigation_steps:
            st.write(f"- {step}")
    else:
        st.info(
            "No investigation steps were returned."
        )

    st.subheader("Log analysis")

    st.write("**Key errors**")

    for error in log_analysis.get(
        "key_errors",
        [],
    ):
        st.write(f"- {error}")

    st.write("**Patterns**")

    for pattern in log_analysis.get(
        "patterns",
        [],
    ):
        st.write(f"- {pattern}")

    st.write("**Suspected components**")

    for component in log_analysis.get(
        "suspected_components",
        [],
    ):
        st.write(f"- {component}")

    st.write("**Evidence**")

    for evidence in log_analysis.get(
        "evidence",
        [],
    ):
        st.write(f"- {evidence}")

    # -----------------------------------------------------
    # One incident-focused runbook only
    # -----------------------------------------------------

    short_runbook = result.get(
        "short_runbook",
        {},
    )

    if short_runbook:
        st.subheader("Runbook")
        st.write(
            f"**Title:** {short_runbook.get('title', 'Incident runbook')}"
        )
        st.write(
            short_runbook.get(
                "summary",
                "No summary available.",
            )
        )

        for step in short_runbook.get("steps", [])[:3]:
            st.write(f"- {step}")
    else:
        st.info(
            "No incident-specific runbook was generated."
        )

    # -----------------------------------------------------
    # Simple root-cause analysis
    # -----------------------------------------------------

    st.subheader("Root-cause analysis")

    st.write(
        f"**Probable root cause:** "
        f"{root_cause.get('root_cause', 'Not available')}"
    )

    st.write(
        f"**Confidence:** "
        f"{root_cause.get('confidence', 0)}%"
    )

    st.write("**Evidence:**")

    root_cause_evidence = root_cause.get(
        "evidence",
        [],
    )

    for evidence in root_cause_evidence:
        st.write(f"- {evidence}")

    # -----------------------------------------------------
    # One remediation
    # -----------------------------------------------------

    st.subheader("Recommended remediation")

    remediation = root_cause.get(
        "recommended_remediation",
        "No remediation recommendation returned.",
    )

    st.info(remediation)

    st.warning(
        "Human approval is required. "
        "No production action will be executed."
    )

    # -----------------------------------------------------
    # Human approval
    # -----------------------------------------------------

    approval_result = (
        st.session_state.approval_result
    )

    approval_completed = (
        approval_result is not None
        or status != "pending_human_approval"
    )

    st.divider()
    st.subheader("Human approval")

    if approval_completed:
        st.info(
            "The approval decision has already been recorded."
        )

    engineer = st.text_input(
        "Approving engineer",
        value="oncall.engineer@company.com",
        disabled=approval_completed,
    )

    comment = st.text_area(
        "Approval comment",
        value="Reviewed the incident evidence.",
        disabled=approval_completed,
    )

    approve_col, reject_col = st.columns(2)

    with approve_col:
        approve_clicked = st.button(
            "Approve simulated remediation",
            type="primary",
            disabled=approval_completed,
            key="approve_button",
        )

    with reject_col:
        reject_clicked = st.button(
            "Reject remediation",
            disabled=approval_completed,
            key="reject_button",
        )

    if approve_clicked or reject_clicked:
        approved = approve_clicked

        with st.spinner(
            "Saving approval decision..."
        ):
            approval = call_approval(
                incident_id=incident_id,
                approved=approved,
                engineer=engineer,
                comment=comment,
            )

        if approval:
            st.session_state.approval_result = approval

            result["status"] = approval.get(
                "status",
                "",
            )

            st.session_state.incident_result = result
            st.rerun()

    if approval_result:
        st.subheader("Approval decision")

        st.write(
            f"**Status:** "
            f"`{approval_result.get('status', '')}`"
        )

        st.success(
            approval_result.get(
                "message",
                "Decision recorded.",
            )
        )

    # -----------------------------------------------------
    # Report
    # -----------------------------------------------------

    if approval_completed:
        st.divider()
        st.subheader("Incident report")

        report_already_generated = (
            st.session_state.report_result is not None
        )

        generate_report_clicked = st.button(
            "Generate incident report",
            type="primary",
            disabled=report_already_generated,
            key="report_button",
        )

        if generate_report_clicked:
            with st.spinner(
                "Generating incident report..."
            ):
                report = call_report(incident_id)

            if report:
                st.session_state.report_result = report
                st.rerun()

        if st.session_state.report_result:
            report_text = st.session_state.report_result.get(
                "report",
                "No report returned.",
            )

            report_summary_rows = [
                {
                    "Section": "Summary",
                    "Value": triage.get(
                        "incident_summary",
                        "No summary returned.",
                    ),
                },
                {
                    "Section": "Root Cause",
                    "Value": root_cause.get(
                        "root_cause",
                        "Not available",
                    ),
                },
                {
                    "Section": "Evidence",
                    "Value": "; ".join(
                        root_cause.get("evidence", [])
                    ) or "No evidence provided.",
                },
                {
                    "Section": "Recommended Remediation",
                    "Value": root_cause.get(
                        "recommended_remediation",
                        "No remediation recommendation returned.",
                    ),
                },
                {
                    "Section": "Approval Status",
                    "Value": (
                        "Approved"
                        if approval_completed and approval_result
                        else "Pending human approval"
                    ),
                },
            ]

            st.subheader("Report summary table")
            render_summary_table(report_summary_rows)

            st.subheader("Report details")
            st.markdown(report_text)