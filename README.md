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

Then open:

- http://127.0.0.1:8502

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
