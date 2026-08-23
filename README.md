# Incident Response Copilot

A lightweight AI-assisted incident response application for triaging incidents, analyzing logs, retrieving relevant knowledge-base runbooks, generating a concise incident-specific runbook, and enforcing human approval before remediation.

## Features
- Submit incident title, description, and logs
- Triage and log analysis using AI agents
- Knowledge-base matching for relevant runbooks
- Generation of a concise, incident-specific runbook
- Root-cause analysis with evidence and confidence
- Human approval workflow
- Incident report generation
- Local working app and separate deployment copy

## Project structure
- app/ - backend logic, orchestration, DB, KB, and model configuration
- ui/ - Streamlit and Gradio front ends for the working local app
- data/ - local SQLite and Chroma data
- tests/ - validation tests for agent parsing and backend candidate resolution
- hf_deploy/ - deployment-safe copy intended for a single-process host such as Hugging Face-compatible Python runtime
- run_app.py - local launcher for backend + Streamlit together

## Local app run
The existing local project remains the working version. From the project root:

```powershell
python run_app.py
```

This starts both services together:

- Backend API: http://127.0.0.1:9002
- Streamlit UI: http://127.0.0.1:8502

Open the Streamlit UI in the browser to submit incidents. The backend continues running in the background and handles investigation, approvals, and report generation.

## API endpoints
The FastAPI backend exposes the following routes:

- POST /incidents - submit an incident for investigation
- GET /incidents - list all stored incidents from SQLite
  - URL: http://127.0.0.1:9002/incidents
- GET /incidents/{incident_id} - fetch one incident by ID
- GET /incidents/{incident_id}/audit - fetch audit events for one incident
- POST /incidents/approval - approve or reject an investigation
- POST /incidents/{incident_id}/report - generate a report for an incident

FastAPI docs are available at:

- http://127.0.0.1:9002/docs

## Incident history and SQLite
Incident records are stored in SQLite so investigations persist across restarts.

Default database path:

```text
./data/incidents.db
```

The database includes:

- incidents - main incident records with title, description, logs, status, timestamps, and result payload
- audit_events - event log for each incident, including investigation and approval activity

To inspect the raised incidents from the terminal:

```powershell
python -c "import sqlite3; conn=sqlite3.connect('data/incidents.db'); print(conn.execute('SELECT incident_id, title, status, created_at FROM incidents ORDER BY created_at DESC').fetchall()); conn.close()"
```

## Deployment copy
A separate deployment-ready folder is included at [hf_deploy](hf_deploy). It is kept separate from the main app so the working local functionality remains unchanged.

This copy is intended for a single-process deployment pattern and uses environment-based cloud configuration rather than the local two-service startup.

## Environment configuration
The project uses environment variables for model and runtime configuration. The current working setup supports:

- local Ollama via `LLM_PROVIDER=local`
- cloud-compatible Ollama endpoint via `LLM_PROVIDER=cloud`

Example values are in [.env.example](.env.example).

## Tech stack
- Python
- FastAPI
- Streamlit
- SQLite
- Chroma
- Agent framework / OpenAI-compatible model integration

## Notes
- The original project remains the working local backup
- The deployment copy is intentionally separate and does not replace the local functionality
- The Streamlit app must target the FastAPI backend URL and should not point to the Streamlit port itself in the local developer setup
- The deployment-safe copy is designed for a single runtime host and cloud-based LLM access
