# Incident Response Copilot

This project is a lightweight AI-assisted incident response workflow for triaging incidents, analyzing logs, retrieving incident-relevant knowledge, generating concise runbooks, and requiring human approval before remediation.

It is designed to help an on-call engineer quickly understand an incident, see likely root cause and evidence, and produce a short actionable response without making automated production changes.

## Latest updates
- Single-file local launcher via run_app.py starts the backend and Streamlit together
- Centralized port and host configuration for backend and frontend stability
- Execution details panel placed beside the incident form in the Streamlit UI
- Telemetry fields include model, provider, TTFT estimate, total latency, and context usage
- TTFT is estimated for non-streaming model calls so it stays meaningful instead of showing 0 ms
- Knowledge-base matching is tightened to keep results concise and incident-focused
- Short runbook generation is limited to the most relevant incident-specific guidance
- Deployment-safe copy is available in hf_deploy while preserving the local working application

## Features
- Submit incident title, description, and logs
- Triage and log analysis using AI agents
- Relevant knowledge-base lookups for incident context
- Short, focused runbook generation
- Root-cause analysis with evidence and confidence score
- Human approval workflow before simulated remediation
- Incident report generation
- SQLite persistence for incident history and audit events
- Local app startup and separate deployment copy

## Project structure
- app/ - backend logic, orchestration, database access, KB lookup, and AI model configuration
- ui/ - Streamlit user interface
- data/ - SQLite incident database and supporting data storage
- tests/ - regression tests covering JSON parsing and telemetry calculations
- hf_deploy/ - deployment-safe copy for a single-process host such as Hugging Face-compatible Python runtime
- run_app.py - local launcher for backend + Streamlit together
- .env.example - example environment configuration for local or cloud model access
- Example incidents.txt - sample incidents for testing the workflow quickly

## Quick start
From the project root, run:

```powershell
python run_app.py
```

This starts:
- Backend API: http://127.0.0.1:9002
- Streamlit UI: http://127.0.0.1:8502

Open the Streamlit app in the browser to submit incidents. The backend handles the investigation flow, approval, and report generation.

## API endpoints
The FastAPI backend exposes these routes:

- POST /incidents - submit an incident for investigation
- GET /incidents - list all incident records in SQLite
- GET /incidents/{incident_id} - fetch one incident by ID
- GET /incidents/{incident_id}/audit - fetch audit events for one incident
- POST /incidents/approval - approve or reject an investigation
- POST /incidents/{incident_id}/report - generate a report

Open the interactive docs here:
- http://127.0.0.1:9002/docs

## Incident history and SQLite storage
Incident data is stored in SQLite so results persist across runs.

Default path:

```text
./data/incidents.db
```

The database stores:
- incidents - incident metadata, payload, status, and timestamps
- audit_events - event trail for investigation and approval actions

Sample query to inspect incidents from the terminal:

```powershell
python -c "import sqlite3; conn=sqlite3.connect('data/incidents.db'); print(conn.execute('SELECT incident_id, title, status, created_at FROM incidents ORDER BY created_at DESC').fetchall()); conn.close()"
```

## Example incidents
A ready-to-use sample set is included in [Example incidents.txt](Example%20incidents.txt). These can be used to raise incidents quickly and validate the full triage workflow.

## UI behavior and telemetry
The Streamlit page now shows an execution details panel beside the form. It includes:
- model name
- provider
- TTFT estimate
- total latency
- context usage percentage

Note: the current model integration is non-streaming end-to-end, so the TTFT is estimated rather than measured from an actual token stream. This keeps the metric realistic without requiring a true streaming backend path.

## Environment configuration
The app uses environment variables for model and runtime configuration.

Current supported modes:
- local Ollama via LLM_PROVIDER=local
- cloud-compatible OpenAI-style Ollama endpoint via LLM_PROVIDER=cloud

Example configuration is in [.env.example](.env.example).

## Deployment copy
A separate deployment-oriented copy is kept in [hf_deploy](hf_deploy). This remains separate from the working local application so the local project can continue to function normally while a deployment-safe version is maintained for hosting.

## Tech stack
- Python
- FastAPI
- Streamlit
- SQLite
- Chroma-like KB storage
- OpenAI-compatible agent framework and model integration

## Notes
- The local app remains the working version and is the one used for day-to-day development
- The deployment folder is intentionally separate and does not replace the working project
- The Streamlit app must call the backend API URL rather than using the Streamlit port directly in the local setup
- Production-style action is intentionally not executed; the workflow is approval-driven and safe by design
