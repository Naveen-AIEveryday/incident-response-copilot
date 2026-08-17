import sys
from pathlib import Path

import requests
import streamlit as st


# Add the root project directory to the Python import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import API_URL


st.set_page_config(
    page_title="Incident Response Copilot",
    page_icon="AI",
    layout="wide",
)

st.title("Agentic IT Incident Response Copilot")
st.caption(
    "Human approval is required before simulated remediation."
)


# ---------------------------------------------------------
# API helper functions
# ---------------------------------------------------------

def submit_incident(
    title: str,
    description: str,
    logs: str,
):
    response = requests.post(
        f"{API_URL}/incidents",
        json={
            "title": title,
            "description": description,
            "logs": logs,
        },
        timeout=180,
    )

    if response.status_code != 200:
        st.error(f"Unable to investigate incident: {response.text}")
        return None

    return response.json()


def approve_remediation(
    incident_id: str,
    approved: bool,
    engineer: str,
    comment: str,
):
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
        st.error(f"Unable to save approval decision: {response.text}")
        return None

    return response.json()


def generate_report(incident_id: str):
    response = requests.post(
        f"{API_URL}/incidents/{incident_id}/report",
        timeout=180,
    )

    if response.status_code != 200:
        st.error(f"Unable to generate report: {response.text}")
        return None

    return response.json()


# ---------------------------------------------------------
# Streamlit session state
# ---------------------------------------------------------

if "incident_result" not in st.session_state:
    st.session_state.incident_result = None

if "approval_result" not in st.session_state:
    st.session_state.approval_result = None

if "report_result" not in st.session_state:
    st.session_state.report_result = None

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False


# ---------------------------------------------------------
# Incident submission form
# ---------------------------------------------------------

with st.form("incident_form"):
    st.subheader("Submit an incident")

    title = st.text_input(
        "Incident title",
        value="Payment API high error rate",
    )

    description = st.text_area(
        "Incident description",
        value=(
            "Customers cannot complete payments. "
            "The error rate increased after a deployment."
        ),
        height=100,
    )

    logs = st.text_area(
        "Incident logs",
        value=(
            "2026-08-10 10:02:11 ERROR payment-api "
            "Database connection timeout. Pool exhausted.\n"
            "2026-08-10 10:02:15 ERROR payment-api "
            "Failed to acquire connection from database pool.\n"
            "2026-08-10 10:03:01 WARN payment-api "
            "Request queue increasing. HTTP 500 rate is 28 percent."
        ),
        height=180,
    )

    investigate_button = st.form_submit_button(
        "Investigate incident",
        type="primary",
    )


if investigate_button:
    with st.spinner("Agents are investigating the incident..."):
        new_result = submit_incident(
            title=title,
            description=description,
            logs=logs,
        )

    if new_result:
        # Reset all previous approval and report information
        # when a new incident is submitted.
        st.session_state.incident_result = new_result
        st.session_state.approval_result = None
        st.session_state.report_result = None
        st.session_state.report_generated = False

        st.success("Incident investigation completed.")
        st.rerun()


# ---------------------------------------------------------
# Display incident analysis
# ---------------------------------------------------------

result = st.session_state.incident_result

if result:
    st.divider()
    st.subheader("Incident investigation")

    incident_id = result["incident_id"]
    current_status = result["status"]

    st.write(f"**Incident ID:** `{incident_id}`")
    st.write(f"**Status:** `{current_status}`")

    triage = result.get("triage", {})
    log_analysis = result.get("log_analysis", {})
    root_cause = result.get("root_cause_analysis", {})

    hypotheses = root_cause.get(
        "root_cause_hypotheses",
        [],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Severity",
            str(triage.get("severity", "unknown")).upper(),
        )

    with col2:
        st.metric(
            "Affected service",
            triage.get("affected_service", "unknown"),
        )

    with col3:
        st.metric(
            "Root cause hypotheses",
            len(hypotheses),
        )

    st.subheader("Incident summary")
    st.write(
        triage.get(
            "incident_summary",
            "No incident summary was returned.",
        )
    )

    st.subheader("Initial investigation steps")

    for step in triage.get("initial_investigation_steps", []):
        st.write(f"- {step}")

    st.subheader("Log analysis")

    st.write("**Key errors**")

    for error in log_analysis.get("key_errors", []):
        st.write(f"- {error}")

    st.write("**Patterns**")

    for pattern in log_analysis.get("patterns", []):
        st.write(f"- {pattern}")

    st.write("**Suspected components**")

    for component in log_analysis.get("suspected_components", []):
        st.write(f"- {component}")

    st.write("**Evidence**")

    for evidence in log_analysis.get("evidence", []):
        st.write(f"- {evidence}")

    st.subheader("Knowledge-base matches")

    knowledge_matches = result.get("knowledge_matches", [])

    for match in knowledge_matches:
        with st.expander(
            f"{match.get('title', 'Untitled document')} "
            f"({match.get('document_type', 'unknown')})"
        ):
            st.write(match.get("content", ""))

    st.subheader("Root-cause hypotheses")

    if hypotheses:
        for index, hypothesis in enumerate(hypotheses, start=1):
            cause = hypothesis.get("cause", "Unknown cause")
            confidence = hypothesis.get("confidence", 0)

            st.markdown(
                f"**{index}. {cause}** "
                f"- {confidence}% confidence"
            )

            for evidence in hypothesis.get("evidence", []):
                st.write(f"- Evidence: {evidence}")
    else:
        st.info("No root-cause hypotheses were returned.")

    st.subheader("Recommended remediation")

    remediation_steps = root_cause.get(
        "recommended_remediation",
        [],
    )

    for action in remediation_steps:
        st.write(f"- {action}")

    st.warning(
        "This capstone project uses simulated remediation only. "
        "No production action is executed."
    )

    # ---------------------------------------------------------
    # Human-in-the-Loop approval
    # ---------------------------------------------------------

    st.divider()
    st.subheader("Human approval")

    approval_result = st.session_state.approval_result

    # The approval controls are disabled after either:
    # 1. Approving remediation
    # 2. Rejecting remediation
    approval_completed = (
        approval_result is not None
        or current_status != "pending_human_approval"
    )

    if approval_completed:
        st.info(
            "The human approval decision has already been recorded. "
            "Approval controls are disabled."
        )

    engineer = st.text_input(
        "Approving engineer",
        value="oncall.engineer@company.com",
        disabled=approval_completed,
    )

    comment = st.text_area(
        "Approval comment",
        value=(
            "Reviewed incident evidence and "
            "runbook recommendations."
        ),
        disabled=approval_completed,
    )

    approval_col, rejection_col = st.columns(2)

    with approval_col:
        approve_clicked = st.button(
            "Approve simulated remediation",
            type="primary",
            disabled=approval_completed,
            key="approve_remediation_button",
        )

    with rejection_col:
        reject_clicked = st.button(
            "Reject remediation",
            disabled=approval_completed,
            key="reject_remediation_button",
        )

    if approve_clicked:
        with st.spinner("Recording approval decision..."):
            approval_response = approve_remediation(
                incident_id=incident_id,
                approved=True,
                engineer=engineer,
                comment=comment,
            )

        if approval_response:
            st.session_state.approval_result = approval_response

            # Update local UI state so buttons are disabled on rerun.
            result["status"] = approval_response["status"]
            st.session_state.incident_result = result

            st.rerun()

    if reject_clicked:
        with st.spinner("Recording rejection decision..."):
            approval_response = approve_remediation(
                incident_id=incident_id,
                approved=False,
                engineer=engineer,
                comment=comment,
            )

        if approval_response:
            st.session_state.approval_result = approval_response

            # Update local UI state so buttons are disabled on rerun.
            result["status"] = approval_response["status"]
            st.session_state.incident_result = result

            st.rerun()

    # Display the recorded human decision.
    approval_result = st.session_state.approval_result

    if approval_result:
        st.subheader("Approval decision")
        st.write(f"**Status:** `{approval_result['status']}`")
        st.success(approval_result["message"])

    # ---------------------------------------------------------
    # Report generation
    # ---------------------------------------------------------

    if approval_completed:
        st.divider()
        st.subheader("Incident report")

        report_button_disabled = st.session_state.report_generated

        if st.session_state.report_generated:
            st.info(
                "The incident report has already been generated. "
                "The report button is disabled."
            )

        generate_report_clicked = st.button(
            "Generate incident report",
            type="primary",
            disabled=report_button_disabled,
            key="generate_report_button",
        )

        if generate_report_clicked:
            with st.spinner("Generating incident report..."):
                report_response = generate_report(incident_id)

            if report_response:
                st.session_state.report_result = report_response
                st.session_state.report_generated = True
                st.rerun()

        report_result = st.session_state.report_result

        if report_result:
            st.markdown(report_result["report"])