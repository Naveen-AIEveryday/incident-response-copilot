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
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Agentic IT Incident Response Copilot")
st.caption(
    "AI-assisted multi-agent incident investigation with ChromaDB knowledge retrieval and human approval."
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stHorizontalBlock"] > div {
        align-items: flex-start;
    }
    .badge-critical { background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
    .badge-high { background-color: #ffedd5; color: #9a3412; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
    .badge-medium { background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
    .badge-low { background-color: #e0f2fe; color: #075985; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Session state initialization
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
def call_investigation(title: str, description: str, logs: str):
    try:
        response = requests.post(
            f"{API_URL}/incidents",
            json={"title": title, "description": description, "logs": logs},
            timeout=180,
        )
        if response.status_code != 200:
            st.error(f"Backend error {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.RequestException as error:
        st.error(f"Could not connect to backend at {API_URL}: {error}")
        return None


def call_approval(incident_id: str, approved: bool, engineer: str, comment: str):
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
            st.error(f"Approval error {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.RequestException as error:
        st.error(f"Could not connect to backend at {API_URL}: {error}")
        return None


def call_report(incident_id: str):
    try:
        response = requests.post(
            f"{API_URL}/incidents/{incident_id}/report",
            timeout=180,
        )
        if response.status_code != 200:
            st.error(f"Report error {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.RequestException as error:
        st.error(f"Could not connect to backend at {API_URL}: {error}")
        return None


def fetch_runbooks():
    try:
        res = requests.get(f"{API_URL}/knowledge/runbooks", timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def search_runbooks(query: str):
    try:
        res = requests.get(f"{API_URL}/knowledge/search", params={"q": query, "limit": 5}, timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def create_runbook(title: str, content: str, doc_type: str, tags: list[str]):
    try:
        res = requests.post(
            f"{API_URL}/knowledge/runbooks",
            json={"title": title, "content": content, "document_type": doc_type, "tags": tags},
            timeout=10,
        )
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def delete_runbook(runbook_id: str):
    try:
        res = requests.delete(f"{API_URL}/knowledge/runbooks/{runbook_id}", timeout=10)
        return res.status_code == 200
    except Exception:
        return False


def fetch_incidents(status: str | None = None, search: str | None = None):
    try:
        params = {}
        if status and status != "all":
            params["status"] = status
        if search:
            params["search"] = search
        res = requests.get(f"{API_URL}/incidents", params=params, timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []


def fetch_incident_audit(incident_id: str):
    try:
        res = requests.get(f"{API_URL}/incidents/{incident_id}/audit", timeout=10)
        return res.json() if res.status_code == 200 else {"events": []}
    except Exception:
        return {"events": []}


def render_summary_table(rows: list[dict[str, str]]) -> None:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def stream_text_chunks(text: str, chunk_size: int = 30):
    if not text:
        yield "No output returned."
        return
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]


def render_agent_telemetry(label: str, telemetry: dict | None) -> None:
    if not telemetry:
        return
    st.markdown(
        f"<div style='border:1px solid #3a3f51; border-radius:10px; padding:10px; background:#101827; margin-bottom:8px;'>"
        f"<div style='font-size:0.8rem; font-weight:700; color:#dfe7ff; margin-bottom:4px;'>{label}</div>"
        f"<div style='font-size:0.75rem; color:#c7d2fe;'>Model: <b>{telemetry.get('model', 'n/a')}</b> | Provider: <b>{telemetry.get('provider', 'n/a')}</b></div>"
        f"<div style='font-size:0.75rem; color:#c7d2fe;'>TTFT (est.): <b>{telemetry.get('ttft_ms', 0)} ms</b> | Latency: <b>{telemetry.get('total_ms', 0)} ms</b></div>"
        f"<div style='font-size:0.75rem; color:#c7d2fe;'>Context Window Usage: <b>{telemetry.get('context_usage_percent', 0)}%</b></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# UI TABS NAVIGATION
# ---------------------------------------------------------
tab_investigate, tab_runbooks, tab_history = st.tabs([
    "🚨 Incident Investigation & Approval",
    "📚 Knowledge Base & Runbooks",
    "📊 Incident History & Audit Trail",
])

# =========================================================
# TAB 1: Incident Investigation & Approval
# =========================================================
with tab_investigate:
    SAMPLE_INCIDENTS = {
        "Custom Incident": {
            "title": "",
            "description": "",
            "logs": "",
        },
        "Python PATH / VS Code Interpreter Failure": {
            "title": "Python is not recognized in VS Code",
            "description": "Python is installed on Windows, but the python command fails in the VS Code integrated terminal.",
            "logs": "'python' is not recognized as an internal or external command, operable program or batch file.\nVS Code cannot identify the interpreter in .venv.",
        },
        "Payment API Database Connection Pool Exhaustion": {
            "title": "Payment API high error rate after deployment",
            "description": "Customers cannot complete checkout payments. 500 error rate surged to 30% following the v2.4 retry feature deployment.",
            "logs": "ERROR payment-api: Database connection timeout\nERROR payment-api: Connection pool exhausted (max 50 connections reached)\nWARN payment-api: HTTP 500 rate is 28 percent",
        },
        "Chrome Website Connection Timeout / DNS Failure": {
            "title": "Internal portal website not loading in Chrome",
            "description": "Users are encountering a blank page and connection timeouts when accessing the internal portal in Google Chrome.",
            "logs": "net::ERR_CONNECTION_TIMED_OUT\nDNS_PROBE_FINISHED_NXDOMAIN\nHost portal.internal.company could not be resolved.",
        },
        "Memory Leak & OOMKilled Service Spike": {
            "title": "Worker service pod crashing with OutOfMemoryError",
            "description": "Data processing worker pod restarts continuously under queue load.",
            "logs": "java.lang.OutOfMemoryError: Java heap space\nKubelet: Container worker-service exceeded memory limit (2048Mi) - OOMKilled",
        },
    }

    selected_sample = st.selectbox(
        "⚡ Quick Load Sample Scenario:",
        list(SAMPLE_INCIDENTS.keys()),
        index=1,
    )
    preset = SAMPLE_INCIDENTS[selected_sample]

    form_col, telemetry_col = st.columns([2.6, 1.2])

    with form_col:
        with st.form("incident_form"):
            st.subheader("Submit Incident for AI Investigation")

            title_val = preset["title"] if preset["title"] else "Python is not recognized in VS Code"
            desc_val = preset["description"] if preset["description"] else "Python command fails in terminal."
            logs_val = preset["logs"] if preset["logs"] else "'python' is not recognized as an internal or external command."

            title = st.text_input("Incident Title", value=title_val)
            description = st.text_area("Incident Description", value=desc_val, height=90)
            logs = st.text_area("Error Logs & Stack Traces", value=logs_val, height=140)

            investigate_clicked = st.form_submit_button("🔍 Run Multi-Agent Investigation", type="primary")

    with telemetry_col:
        st.markdown("<div style='font-weight:700; margin-bottom:8px;'>AI Execution Details</div>", unsafe_allow_html=True)
        res = st.session_state.incident_result
        if res:
            render_agent_telemetry("Triage Agent", res.get("triage", {}).get("_telemetry"))
            render_agent_telemetry("Log Analysis Agent", res.get("log_analysis", {}).get("_telemetry"))
            render_agent_telemetry("Short Runbook Agent", res.get("short_runbook", {}).get("_telemetry"))
            render_agent_telemetry("Root Cause Agent", res.get("root_cause_analysis", {}).get("_telemetry"))
        else:
            st.info("Submit an incident to inspect multi-agent timing and context metrics.")

    if investigate_clicked:
        prog_bar = st.progress(0, text="Initializing investigation...")
        prog_bar.progress(25, text="1/4 Triaging incident & analyzing error logs...")
        result = call_investigation(title=title, description=description, logs=logs)
        prog_bar.progress(100, text="Investigation complete!")

        if result:
            st.session_state.incident_result = result
            st.session_state.approval_result = None
            st.session_state.report_result = None
            st.success("✅ Multi-agent investigation completed successfully.")
            st.rerun()

    # Render Result
    result = st.session_state.incident_result
    if result:
        st.divider()
        st.markdown("### 📋 Investigation Findings")

        inc_id = result.get("incident_id", "")
        status = result.get("status", "")
        triage = result.get("triage", {})
        log_analysis = result.get("log_analysis", {})
        short_runbook = result.get("short_runbook", {})
        root_cause = result.get("root_cause_analysis", {})
        suggested_commands = result.get("suggested_commands", []) or root_cause.get("suggested_commands", [])

        # Top summary cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Incident ID", inc_id[:8] + "...")
        c2.metric("Severity", str(triage.get("severity", "MEDIUM")).upper())
        c3.metric("Affected Service", triage.get("affected_service", "Unknown"))
        c4.metric("Diagnosis Confidence", f"{root_cause.get('confidence', 0)}%")

        # Summary Table
        st.subheader("Triage Overview")
        render_summary_table([
            {"Section": "Severity", "Detail": str(triage.get("severity", "")).upper()},
            {"Section": "Affected Service", "Detail": str(triage.get("affected_service", ""))},
            {"Section": "Incident Summary", "Detail": str(triage.get("incident_summary", ""))},
        ])

        with st.expander("🔍 Log Analysis & Extracted Evidence", expanded=True):
            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown("**Key Errors Identified:**")
                for err in log_analysis.get("key_errors", []):
                    st.markdown(f"- `{err}`")
                st.markdown("**Suspected Components:**")
                for comp in log_analysis.get("suspected_components", []):
                    st.markdown(f"- **{comp}**")
            with ec2:
                st.markdown("**Failure Patterns:**")
                for pat in log_analysis.get("patterns", []):
                    st.markdown(f"- {pat}")
                st.markdown("**Log Evidence:**")
                for ev in log_analysis.get("evidence", []):
                    st.markdown(f"- *{ev}*")

        # Actionable Runbook
        if short_runbook:
            st.subheader(f"📖 Action Runbook: {short_runbook.get('title', 'Troubleshooting Plan')}")
            st.info(short_runbook.get("summary", ""))
            for idx, step in enumerate(short_runbook.get("steps", []), 1):
                st.markdown(f"**Step {idx}:** {step}")

        # Root Cause & Safe Commands
        st.subheader("🎯 Probable Root Cause & Safe Diagnostics")
        st.markdown(f"**Root Cause:** {root_cause.get('root_cause', 'Unknown')}")

        if suggested_commands:
            st.markdown("**Recommended Safe Diagnostic Commands (Read-Only):**")
            for cmd in suggested_commands:
                st.code(cmd, language="bash")

        st.subheader("💡 Recommended Remediation")
        st.success(root_cause.get("recommended_remediation", "No remediation proposed."))
        st.warning("⚠️ **Safety Notice:** Human approval is strictly required before any action is executed.")

        # Human Approval Gate
        st.divider()
        st.subheader("✍️ Human-in-the-Loop Approval")

        approval_result = st.session_state.approval_result
        approval_completed = approval_result is not None or status != "pending_human_approval"

        if approval_completed:
            st.info("The approval decision for this investigation has been recorded in SQLite.")

        eng_email = st.text_input("Approving Engineer Email", value="unaveen0511@gmail.com", disabled=approval_completed)
        app_comment = st.text_area("Review Comments", value="Verified evidence and diagnostic findings.", disabled=approval_completed)

        col_app, col_rej = st.columns(2)
        with col_app:
            btn_app = st.button("✅ Approve Simulated Remediation", type="primary", disabled=approval_completed)
        with col_rej:
            btn_rej = st.button("❌ Reject Remediation", disabled=approval_completed)

        if btn_app or btn_rej:
            is_approved = btn_app
            with st.spinner("Recording approval decision..."):
                app_res = call_approval(inc_id, is_approved, eng_email, app_comment)
            if app_res:
                st.session_state.approval_result = app_res
                result["status"] = app_res.get("status", "")
                st.session_state.incident_result = result
                st.rerun()

        if approval_completed:
            st.divider()
            st.subheader("📄 Post-Mortem Incident Report")
            if st.button("📑 Generate Official Incident Report", type="primary", key="btn_gen_rep"):
                with st.spinner("Generating post-mortem report..."):
                    rep = call_report(inc_id)
                if rep:
                    st.session_state.report_result = rep
                    st.rerun()

            if st.session_state.report_result:
                st.markdown(st.session_state.report_result.get("report", "No report generated."))


# =========================================================
# TAB 2: Knowledge Base & Runbooks Manager
# =========================================================
with tab_runbooks:
    st.subheader("📚 ChromaDB Knowledge Base & Runbooks")
    st.caption("Inspect indexed operational runbooks, run semantic search queries, or ingest new runbooks dynamically.")

    s_col, _ = st.columns([3, 1])
    with s_col:
        search_q = st.text_input("🔎 Test Semantic & Hybrid Search across Knowledge Base:", placeholder="e.g. database timeout or python command error")

    if search_q:
        search_res = search_runbooks(search_q)
        st.markdown(f"**Found {len(search_res)} matching runbooks:**")
        for doc in search_res:
            with st.expander(f"📖 {doc.get('title')} (Score: {doc.get('score', 0)})"):
                st.markdown(f"**Document Type:** `{doc.get('document_type', 'runbook')}` | **Tags:** `{doc.get('tags', [])}`")
                st.text(doc.get("content", ""))

    st.divider()
    rb_col1, rb_col2 = st.columns([2, 1.2])

    with rb_col1:
        st.subheader("Indexed Runbooks Repository")
        runbooks_list = fetch_runbooks()
        if runbooks_list:
            for rb in runbooks_list:
                with st.expander(f"📄 {rb.get('title')} (`{rb.get('id')}`)", expanded=False):
                    st.markdown(f"**Type:** `{rb.get('document_type')}` | **Tags:** `{rb.get('tags', [])}`")
                    st.text(rb.get("content", ""))
                    if st.button(f"🗑️ Delete", key=f"del_{rb.get('id')}"):
                        if delete_runbook(rb.get("id")):
                            st.success(f"Deleted runbook {rb.get('title')}")
                            st.rerun()
        else:
            st.info("No runbooks found.")

    with rb_col2:
        st.subheader("➕ Ingest Custom Runbook")
        with st.form("add_runbook_form"):
            new_title = st.text_input("Runbook Title", placeholder="e.g. Redis Cluster Failover Runbook")
            new_type = st.selectbox("Document Type", ["runbook", "historical_incident", "standard_operating_procedure"])
            new_tags = st.text_input("Tags (comma separated)", placeholder="redis, cache, timeout")
            new_content = st.text_area("Runbook Content / Steps", placeholder="Symptoms:\n...\nResolutions:\n...", height=180)
            add_btn = st.form_submit_button("Ingest into ChromaDB", type="primary")

            if add_btn:
                if new_title and new_content:
                    tags_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                    res = create_runbook(new_title, new_content, new_type, tags_list)
                    if res:
                        st.success(f"✅ Ingested '{new_title}' successfully!")
                        st.rerun()
                else:
                    st.error("Title and Content are required.")


# =========================================================
# TAB 3: Incident History & Audit Trail Explorer
# =========================================================
with tab_history:
    st.subheader("📊 Incident History & Audit Trails")
    st.caption("Review all past investigated incidents and trace chronological audit events in SQLite.")

    fc1, fc2, fc3 = st.columns([1.5, 2, 1])
    with fc1:
        stat_filter = st.selectbox("Filter Status", ["all", "pending_human_approval", "remediation_approved", "remediation_rejected", "investigating"])
    with fc2:
        search_filter = st.text_input("Search History", placeholder="Search title or logs...")
    with fc3:
        if st.button("🔄 Refresh History"):
            st.rerun()

    incidents = fetch_incidents(status=stat_filter, search=search_filter)

    if incidents:
        st.markdown(f"**Showing {len(incidents)} Incidents:**")
        for inc in incidents:
            inc_id = inc.get("incident_id", "")
            with st.expander(f"🚨 {inc.get('title')} — Status: `{inc.get('status')}` ({inc.get('created_at')[:19]})"):
                st.markdown(f"**ID:** `{inc_id}` | **Status:** `{inc.get('status')}` | **Created:** `{inc.get('created_at')}`")
                st.markdown(f"**Description:** {inc.get('description')}")
                st.text(f"Logs:\n{inc.get('logs')}")

                # Audit Events
                audit_data = fetch_incident_audit(inc_id)
                events = audit_data.get("events", [])
                if events:
                    st.markdown("**Chronological Audit Events:**")
                    event_rows = [
                        {"Timestamp": ev.get("created_at")[:19], "Event Type": ev.get("event_type"), "Details Summary": str(ev.get("details"))[:80] + "..."}
                        for ev in events
                    ]
                    st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No past incidents match the current filters.")