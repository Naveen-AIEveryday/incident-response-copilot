import json
import sys
from pathlib import Path
from typing import Any

import gradio as gr
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    API_URL,
    GRADIO_HOST,
    GRADIO_PORT,
)

PRESETS = {
    "🐍 Python VS Code PATH": {
        "title": "Python is not recognized in VS Code",
        "description": "Python is installed, but the Python command is not recognized in the VS Code terminal.",
        "logs": "'python' is not recognized as an internal or external command, operable program or batch file.\nVS Code cannot locate python.exe.",
    },
    "🗄️ 500 DB Pool Exhaustion": {
        "title": "HTTP 500 Spike on Checkout API",
        "description": "Users receive 500 Internal Server Error when completing purchases after new deployment.",
        "logs": "TimeoutException: Connection pool exhausted (50/50 connections active).\nPOST /api/checkout 500 Internal Server Error",
    },
    "🌐 Chrome DNS NXDOMAIN": {
        "title": "Internal Portal not loading in Google Chrome",
        "description": "Engineers report blank pages and DNS errors when accessing internal portal.",
        "logs": "ERR_CONNECTION_TIMED_OUT\nDNS_PROBE_FINISHED_NXDOMAIN for internal.corp.net",
    },
}


def call_investigate(title: str, description: str, logs: str):
    if not title or not description:
        gr.Warning("Incident title and description are required.")
        return [None] * 12

    try:
        res = requests.post(
            f"{API_URL}/incidents",
            json={"title": title, "description": description, "logs": logs},
            timeout=180,
        )
        res.raise_for_status()
        data = res.json()

        inc_id = data.get("incident_id", "")
        status = data.get("status", "")
        triage = data.get("triage", {})
        log_analysis = data.get("log_analysis", {})
        short_runbook = data.get("short_runbook", {})
        root_cause = data.get("root_cause_analysis", {})
        suggested_cmds = data.get("suggested_commands", []) or root_cause.get("suggested_commands", [])
        kb_matches = data.get("knowledge_matches", [])

        # Format Triage markdown
        severity = str(triage.get("severity", "MEDIUM")).upper()
        triage_md = f"### Severity: **`{severity}`**\n"
        triage_md += f"- **Affected Service:** {triage.get('affected_service', 'N/A')}\n"
        triage_md += f"- **Summary:** {triage.get('incident_summary', '')}\n\n"
        triage_md += "**Initial Steps:**\n"
        for step in triage.get("initial_investigation_steps", []):
            triage_md += f"- {step}\n"

        # Format Log Analysis markdown
        log_md = "**Key Errors:**\n"
        for err in log_analysis.get("key_errors", []):
            log_md += f"- `{err}`\n"
        log_md += "\n**Patterns & Suspected Components:**\n"
        for comp in log_analysis.get("suspected_components", []):
            log_md += f"- `{comp}`\n"
        log_md += "\n**Evidence Snippets:**\n"
        for ev in log_analysis.get("evidence", []):
            log_md += f"> {ev}\n"

        # Format Short Runbook markdown
        rb_md = f"### 📘 {short_runbook.get('title', 'Action Runbook')}\n"
        rb_md += f"*{short_runbook.get('summary', '')}*\n\n"
        for i, stp in enumerate(short_runbook.get("steps", []), 1):
            rb_md += f"{i}. {stp}\n"

        # Format Root Cause markdown
        confidence = root_cause.get("confidence", 50)
        rc_md = f"### 🔍 Probable Root Cause (Confidence: **{confidence}%**)\n"
        rc_md += f"> **{root_cause.get('root_cause', '')}**\n\n"
        rc_md += f"**Recommended Remediation:**\n{root_cause.get('recommended_remediation', '')}\n\n"
        rc_md += f"⚠️ *Human Approval Required: {root_cause.get('requires_human_approval', True)}*"

        # Diagnostic Commands
        cmd_text = "\n".join(suggested_cmds) if suggested_cmds else "# No diagnostic commands suggested"

        # Telemetry
        telemetry = triage.get("_telemetry", {}) or root_cause.get("_telemetry", {})
        tele_md = (
            f"**Model:** `{telemetry.get('model', 'gpt-oss:20b')}` | "
            f"**Provider:** `{telemetry.get('provider', 'cloud')}` | "
            f"**Latency:** `{telemetry.get('total_ms', 0)} ms` | "
            f"**Est. TTFT:** `{telemetry.get('ttft_ms', 0)} ms` | "
            f"**Context Used:** `{telemetry.get('context_usage_percent', 0)}%`"
        )

        kb_json = json.dumps(kb_matches, indent=2)

        return (
            inc_id,
            f"Incident `{inc_id}` — Status: **{status}**",
            triage_md,
            log_md,
            rb_md,
            rc_md,
            cmd_text,
            kb_json,
            tele_md,
            inc_id,  # for approval box
            gr.update(visible=True),  # approval section
            gr.update(visible=True),  # report section
        )
    except Exception as e:
        gr.Error(f"Investigation failed: {str(e)}")
        return [None] * 12


def call_approval(incident_id: str, approved_by: str, decision: str, comment: str):
    if not incident_id:
        gr.Warning("No active incident ID found.")
        return "No incident selected."

    is_approved = (decision == "Approve")
    try:
        res = requests.post(
            f"{API_URL}/incidents/approval",
            json={
                "incident_id": incident_id,
                "approved_by": approved_by,
                "approved": is_approved,
                "comment": comment,
            },
            timeout=30,
        )
        res.raise_for_status()
        data = res.json()
        status = data.get("status", "")
        msg = data.get("message", "")
        return f"✅ **Approval Submitted:** `{status}`\n\n_{msg}_"
    except Exception as e:
        return f"❌ Approval failed: {str(e)}"


def call_report(incident_id: str):
    if not incident_id:
        gr.Warning("No active incident ID found.")
        return "No incident selected."

    try:
        res = requests.post(
            f"{API_URL}/incidents/{incident_id}/report",
            timeout=120,
        )
        res.raise_for_status()
        data = res.json()
        return data.get("report", "No report content generated.")
    except Exception as e:
        return f"❌ Report generation failed: {str(e)}"


def search_kb(query: str):
    if not query:
        return "Please enter a search query."
    try:
        res = requests.get(f"{API_URL}/knowledge/search", params={"q": query, "limit": 5}, timeout=15)
        res.raise_for_status()
        docs = res.json()
        if not docs:
            return "No matching runbooks found."

        out = f"### Found {len(docs)} Matching Runbooks:\n\n"
        for doc in docs:
            out += f"#### 📖 {doc.get('title')} (Match Score: `{doc.get('score', 0)}`)\n"
            out += f"- **Type:** `{doc.get('document_type')}` | **Tags:** `{doc.get('tags', [])}`\n"
            out += f"```text\n{doc.get('content', '')}\n```\n\n---\n"
        return out
    except Exception as e:
        return f"Search failed: {str(e)}"


def list_all_runbooks():
    try:
        res = requests.get(f"{API_URL}/knowledge/runbooks", timeout=15)
        res.raise_for_status()
        docs = res.json()
        if not docs:
            return "No runbooks in repository."

        out = f"### Indexed Runbooks Catalog ({len(docs)} Total):\n\n"
        for doc in docs:
            out += f"**📄 {doc.get('title')}** (`{doc.get('id')}`)\n"
            out += f"- **Type:** `{doc.get('document_type')}` | **Tags:** `{doc.get('tags', [])}`\n"
            out += f"```text\n{doc.get('content', '')}\n```\n\n---\n"
        return out
    except Exception as e:
        return f"Failed to list runbooks: {str(e)}"


def add_custom_runbook(title: str, doc_type: str, tags: str, content: str):
    if not title or not content:
        return "Title and Content are required."
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        res = requests.post(
            f"{API_URL}/knowledge/runbooks",
            json={"title": title, "document_type": doc_type, "tags": tags_list, "content": content},
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
        return f"✅ Successfully ingested runbook '{title}' (`{data.get('id')}`) into ChromaDB!"
    except Exception as e:
        return f"❌ Ingestion failed: {str(e)}"


def list_history_incidents(status_filter: str, search_query: str):
    params: dict[str, Any] = {}
    if status_filter and status_filter != "all":
        params["status"] = status_filter
    if search_query:
        params["search"] = search_query

    try:
        res = requests.get(f"{API_URL}/incidents", params=params, timeout=15)
        res.raise_for_status()
        incs = res.json()
        if not incs:
            return "No incidents found matching criteria."

        out = f"### Incident History ({len(incs)} Records):\n\n"
        for inc in incs:
            inc_id = inc.get("incident_id", "")
            out += f"#### 🚨 {inc.get('title')} — Status: `{inc.get('status')}`\n"
            out += f"- **ID:** `{inc_id}` | **Created:** `{inc.get('created_at', '')[:19]}`\n"
            out += f"- **Description:** {inc.get('description', '')}\n"
            out += f"```text\nLogs: {inc.get('logs', '')}\n```\n\n---\n"
        return out
    except Exception as e:
        return f"Failed to fetch history: {str(e)}"


def load_preset(name: str):
    preset = PRESETS.get(name, {})
    return preset.get("title", ""), preset.get("description", ""), preset.get("logs", "")


# ---------------------------------------------------------------------------
# Gradio Application Layout
# ---------------------------------------------------------------------------

with gr.Blocks(title="Incident Response Copilot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛡️ AI-Powered Agentic Incident Response Copilot")
    gr.Markdown("Autonomous multi-agent investigation, hybrid runbook retrieval, and human-in-the-loop operational safety.")

    with gr.Tabs():
        # TAB 1: Investigation & Approval
        with gr.Tab("🚨 Investigation & Approval"):
            gr.Markdown("### 1. Submit Incident Details")

            with gr.Row():
                preset_dropdown = gr.Dropdown(
                    label="Quick Load Scenario Preset",
                    choices=list(PRESETS.keys()),
                    value="🐍 Python VS Code PATH",
                    interactive=True,
                )
                load_btn = gr.Button("⚡ Load Preset", size="sm")

            with gr.Row():
                in_title = gr.Textbox(label="Incident Title", value=PRESETS["🐍 Python VS Code PATH"]["title"], lines=1)
            with gr.Row():
                in_desc = gr.Textbox(label="Incident Description", value=PRESETS["🐍 Python VS Code PATH"]["description"], lines=3)
            with gr.Row():
                in_logs = gr.Textbox(label="Error Logs / Terminal Output", value=PRESETS["🐍 Python VS Code PATH"]["logs"], lines=4)

            investigate_btn = gr.Button("🔍 Investigate Incident (Multi-Agent)", variant="primary", size="lg")

            out_status = gr.Markdown()
            telemetry_out = gr.Markdown()

            with gr.Row():
                with gr.Column():
                    triage_out = gr.Markdown(label="Triage Assessment")
                with gr.Column():
                    log_out = gr.Markdown(label="SRE Log Analysis")

            with gr.Row():
                with gr.Column():
                    runbook_out = gr.Markdown(label="Short Actionable Runbook")
                with gr.Column():
                    root_cause_out = gr.Markdown(label="Root Cause Diagnosis")

            gr.Markdown("### 🛠️ Suggested Read-Only Diagnostic Commands")
            commands_out = gr.Code(label="Safe Diagnostic Commands (Copyable)", language="shell")

            with gr.Accordion("📚 Relevant Knowledge Base Matches", open=False):
                kb_out = gr.Code(label="ChromaDB Hybrid Matches (JSON)", language="json")

            # Human Approval Gate Section
            with gr.Group(visible=False) as approval_sec:
                gr.Markdown("---")
                gr.Markdown("### 👤 Human-in-the-Loop Remediation Approval Gate")
                with gr.Row():
                    app_inc_id = gr.Textbox(label="Target Incident ID", interactive=False)
                    app_engineer = gr.Textbox(label="Approving Engineer Email", value="unaveen0511@gmail.com")
                    app_decision = gr.Radio(choices=["Approve", "Reject"], label="Decision", value="Approve")
                app_comment = gr.Textbox(label="Engineering Review Comment", value="Approved after reviewing diagnostic commands.")
                submit_approval_btn = gr.Button("✅ Submit Remediation Decision", variant="primary")
                approval_result_out = gr.Markdown()

            # Post-Mortem Report Section
            with gr.Group(visible=False) as report_sec:
                gr.Markdown("---")
                gr.Markdown("### 📄 Post-Mortem Incident Report")
                gen_report_btn = gr.Button("📑 Generate Official Incident Report", variant="secondary")
                report_out = gr.Markdown()

            # Wiring Tab 1 actions
            current_inc_id_state = gr.State()

            load_btn.click(
                fn=load_preset,
                inputs=[preset_dropdown],
                outputs=[in_title, in_desc, in_logs],
            )

            investigate_btn.click(
                fn=call_investigate,
                inputs=[in_title, in_desc, in_logs],
                outputs=[
                    current_inc_id_state,
                    out_status,
                    triage_out,
                    log_out,
                    runbook_out,
                    root_cause_out,
                    commands_out,
                    kb_out,
                    telemetry_out,
                    app_inc_id,
                    approval_sec,
                    report_sec,
                ],
            )

            submit_approval_btn.click(
                fn=call_approval,
                inputs=[app_inc_id, app_engineer, app_decision, app_comment],
                outputs=[approval_result_out],
            )

            gen_report_btn.click(
                fn=call_report,
                inputs=[app_inc_id],
                outputs=[report_out],
            )

        # TAB 2: Knowledge Base & Runbooks Manager
        with gr.Tab("📚 Knowledge Base & Runbooks"):
            gr.Markdown("### 🔎 Test ChromaDB Hybrid Search")
            with gr.Row():
                kb_query = gr.Textbox(label="Search Query", placeholder="e.g. database connection pool exhausted or python command error", scale=4)
                kb_search_btn = gr.Button("Search Knowledge Base", variant="primary", scale=1)
            kb_search_results = gr.Markdown()

            gr.Markdown("---")
            with gr.Row():
                with gr.Column(scale=3):
                    gr.Markdown("### 📖 Indexed Operational Runbooks")
                    refresh_kb_btn = gr.Button("🔄 Refresh Runbooks Catalog")
                    kb_list_out = gr.Markdown()
                with gr.Column(scale=2):
                    gr.Markdown("### ➕ Ingest Custom Runbook into ChromaDB")
                    new_rb_title = gr.Textbox(label="Runbook Title", placeholder="e.g. Redis Eviction Runbook")
                    new_rb_type = gr.Dropdown(label="Document Type", choices=["runbook", "historical_incident", "standard_operating_procedure"], value="runbook")
                    new_rb_tags = gr.Textbox(label="Tags (comma-separated)", placeholder="redis, cache, memory")
                    new_rb_content = gr.Textbox(label="Content & Resolution Steps", placeholder="Symptoms:\n...\nResolutions:\n...", lines=8)
                    add_rb_btn = gr.Button("📥 Ingest into ChromaDB", variant="primary")
                    add_rb_status = gr.Markdown()

            kb_search_btn.click(fn=search_kb, inputs=[kb_query], outputs=[kb_search_results])
            refresh_kb_btn.click(fn=list_all_runbooks, outputs=[kb_list_out])
            add_rb_btn.click(
                fn=add_custom_runbook,
                inputs=[new_rb_title, new_rb_type, new_rb_tags, new_rb_content],
                outputs=[add_rb_status],
            )

        # TAB 3: Incident History & Audit Trail
        with gr.Tab("📊 Incident History & Audit Trail"):
            gr.Markdown("### 🗄️ Query Past Investigated Incidents")
            with gr.Row():
                hist_status = gr.Dropdown(label="Filter Status", choices=["all", "pending_human_approval", "remediation_approved", "remediation_rejected", "investigating"], value="all")
                hist_search = gr.Textbox(label="Search Title / Logs", placeholder="e.g. timeout or python")
                hist_refresh_btn = gr.Button("🔍 Fetch Incidents", variant="primary")

            hist_out = gr.Markdown()
            hist_refresh_btn.click(
                fn=list_history_incidents,
                inputs=[hist_status, hist_search],
                outputs=[hist_out],
            )


def launch():
    demo.launch(
        server_name=GRADIO_HOST,
        server_port=GRADIO_PORT,
        share=False,
    )


if __name__ == "__main__":
    launch()