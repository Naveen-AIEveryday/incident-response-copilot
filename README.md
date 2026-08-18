# Incident Response Copilot

A lightweight AI-assisted incident response application that helps triage incidents, analyze logs, retrieve relevant knowledge-base runbooks, generate a short incident-specific runbook, and support human approval before remediation.

## Features
- Submit incident title, description, and logs
- Triage and log analysis using AI agents
- Knowledge-base matching for relevant runbooks
- Generation of a concise, incident-specific runbook
- Root-cause analysis with evidence and confidence
- Human approval workflow
- Incident report generation
- Streamlit UI and FastAPI backend

## Project structure
- app/ - backend application and orchestration logic
- ui/ - Streamlit and Gradio front ends
- data/ - local database and Chroma storage
- tests/ - validation tests

## Run the app
From the project folder:

```powershell
python run_app.py
```

This starts both services together:

- Backend API: http://127.0.0.1:9002
- Streamlit UI: http://127.0.0.1:8502

Open the Streamlit UI in the browser to submit incidents. The backend continues running in the background and handles investigation, approvals, and report generation.

## Backend endpoints
The FastAPI backend exposes the following main routes:

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
The app stores incident records in SQLite so investigations persist across restarts.

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

## Tech stack
- Python
- FastAPI
- Streamlit
- SQLite
- Chroma
- Agent framework / local model integration

## Notes
- The backend runs on port 9002
- The Streamlit UI runs on port 8502
- The app is designed for human-in-the-loop incident response and simulated remediation only
- The Streamlit app calls the FastAPI backend using the configured API URL; it must not point to the Streamlit port itself
