import sys
from pathlib import Path

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


def investigate(
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

        response.raise_for_status()
        result = response.json()

        triage = result["triage"]
        log_analysis = result["log_analysis"]
        root_cause = result[
            "root_cause_analysis"
        ]

        hypotheses = root_cause.get(
            "root_cause_hypotheses",
            [],
        )

        hypothesis_text = "\n\n".join(
            [
                (
                    f"{index}. {item.get('cause')}\n"
                    f"Confidence: "
                    f"{item.get('confidence')}%\n"
                    f"Evidence: "
                    f"{item.get('evidence')}"
                )
                for index, item in enumerate(
                    hypotheses,
                    start=1,
                )
            ]
        )

        output = f"""
Incident ID:
{result["incident_id"]}

Status:
{result["status"]}

Severity:
{triage.get("severity")}

Affected service:
{triage.get("affected_service")}

Summary:
{triage.get("incident_summary")}

Key errors:
{log_analysis.get("key_errors")}

Patterns:
{log_analysis.get("patterns")}

Root-cause hypotheses:
{hypothesis_text}

Recommended remediation:
{root_cause.get("recommended_remediation")}

Human approval is required.
No production action was executed.
"""

        return (
            output,
            result["incident_id"],
            gr.update(interactive=True),
            gr.update(interactive=True),
        )

    except Exception as error:
        return (
            f"Backend error: {error}",
            "",
            gr.update(interactive=False),
            gr.update(interactive=False),
        )


def submit_approval(
    incident_id: str,
    engineer: str,
    comment: str,
    approved: bool,
):
    if not incident_id:
        return (
            "No incident ID is available.",
            gr.update(interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=False),
        )

    try:
        response = requests.post(
            f"{API_URL}/incidents/approval",
            json={
                "incident_id": incident_id,
                "approved_by": engineer,
                "approved": approved,
                "comment": comment,
            },
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()

        return (
            (
                f"Status: {result['status']}\n\n"
                f"{result['message']}"
            ),
            gr.update(interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=True),
        )

    except Exception as error:
        return (
            f"Approval error: {error}",
            gr.update(interactive=True),
            gr.update(interactive=True),
            gr.update(interactive=False),
        )


def generate_report(
    incident_id: str,
):
    if not incident_id:
        return (
            "No incident ID is available.",
            gr.update(interactive=False),
        )

    try:
        response = requests.post(
            f"{API_URL}/incidents/{incident_id}/report",
            timeout=180,
        )

        response.raise_for_status()
        result = response.json()

        return (
            result["report"],
            gr.update(interactive=False),
        )

    except Exception as error:
        return (
            f"Report error: {error}",
            gr.update(interactive=True),
        )


with gr.Blocks(
    title="Incident Response Copilot",
) as demo:
    gr.Markdown(
        """
# Agentic IT Incident Response Copilot

Analyze an incident, review recommendations,
and approve or reject simulated remediation.
        """
    )

    title = gr.Textbox(
        label="Incident title",
        value="Payment API high error rate",
    )

    description = gr.Textbox(
        label="Incident description",
        value=(
            "Customers cannot complete payments. "
            "The error rate increased after deployment."
        ),
        lines=4,
    )

    logs = gr.Textbox(
        label="Incident logs",
        value=(
            "ERROR payment-api "
            "Database connection timeout\n"
            "ERROR payment-api "
            "Connection pool exhausted\n"
            "WARN payment-api "
            "HTTP 500 rate is 28 percent"
        ),
        lines=8,
    )

    investigate_button = gr.Button(
        "Investigate incident",
        variant="primary",
    )

    investigation_output = gr.Textbox(
        label="Investigation result",
        lines=20,
    )

    incident_id = gr.Textbox(
        label="Incident ID",
        interactive=False,
    )

    gr.Markdown("## Human approval")

    engineer = gr.Textbox(
        label="Approving engineer",
        value="unaveen0511@gmail.com",
    )

    comment = gr.Textbox(
        label="Approval comment",
        value="Reviewed the incident evidence.",
        lines=3,
    )

    with gr.Row():
        approve_button = gr.Button(
            "Approve simulated remediation",
            variant="primary",
            interactive=False,
        )

        reject_button = gr.Button(
            "Reject remediation",
            interactive=False,
        )

    approval_output = gr.Textbox(
        label="Approval decision",
        lines=5,
    )

    report_button = gr.Button(
        "Generate incident report",
        interactive=False,
    )

    report_output = gr.Markdown()

    investigate_button.click(
        fn=investigate,
        inputs=[
            title,
            description,
            logs,
        ],
        outputs=[
            investigation_output,
            incident_id,
            approve_button,
            reject_button,
        ],
    )

    approve_button.click(
        fn=lambda incident, user, note: submit_approval(
            incident,
            user,
            note,
            True,
        ),
        inputs=[
            incident_id,
            engineer,
            comment,
        ],
        outputs=[
            approval_output,
            approve_button,
            reject_button,
            report_button,
        ],
    )

    reject_button.click(
        fn=lambda incident, user, note: submit_approval(
            incident,
            user,
            note,
            False,
        ),
        inputs=[
            incident_id,
            engineer,
            comment,
        ],
        outputs=[
            approval_output,
            approve_button,
            reject_button,
            report_button,
        ],
    )

    report_button.click(
        fn=generate_report,
        inputs=[
            incident_id,
        ],
        outputs=[
            report_output,
            report_button,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        server_name=GRADIO_HOST,
        server_port=GRADIO_PORT,
    )