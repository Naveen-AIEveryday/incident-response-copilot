# High-Level Project Report

## Project Purpose
This project is an AI-assisted incident response tool. It helps teams triage incidents, analyze logs, find relevant knowledge-base runbooks, generate a short troubleshooting plan, and capture human approval before any remediation is suggested.

## What the System Does
The application takes an incident title, description, and logs, then performs the following:

- classifies the incident severity and service impact
- analyzes the provided logs for errors and patterns
- searches the knowledge base for relevant runbooks
- creates a short, incident-specific action plan
- identifies a likely root cause with supporting evidence
- waits for human approval before finishing the workflow
- produces a final incident report

## Main Components

### 1. Application Logic
The core business logic is in:
- [app/agents.py](app/agents.py) — AI agent orchestration and JSON response parsing
- [app/orchestrator.py](app/orchestrator.py) — end-to-end incident workflow
- [app/models.py](app/models.py) — request and response models

### 2. Data and Knowledge Base
The application stores incidents and audit history, and it also keeps a local knowledge base of runbooks:
- [app/database.py](app/database.py) — SQLite storage for incidents and audit events
- [app/knowledge_base.py](app/knowledge_base.py) — support content for runbook matching

### 3. API and UI
The project exposes a FastAPI backend and user interfaces:
- [app/main.py](app/main.py) — backend app entry point
- [app/routes.py](app/routes.py) — API endpoints
- [ui/streamlit_app.py](ui/streamlit_app.py) — main Streamlit UI
- [ui/gradio_app.py](ui/gradio_app.py) — alternative interface

### 4. Configuration and Runtime
The runtime setup, ports, and model configuration are defined in:
- [app/config.py](app/config.py)
- [run_app.py](run_app.py)
- [.env](.env)
- [.env.example](.env.example)

### 5. Deployment Copy
The project includes a separate deployment-friendly version to keep the original working app safe and unchanged:
- [hf_deploy](hf_deploy)

## Workflow Summary
1. User submits incident details.
2. The system triages the issue.
3. Logs are analyzed for key errors and patterns.
4. Relevant knowledge-base matches are retrieved.
5. A short action-oriented runbook is created.
6. A root-cause summary is generated.
7. Human approval is requested.
8. A final report is created for review.

## Current Architecture Style
This is a lightweight multi-agent workflow application. It combines:
- Python backend services
- AI-powered reasoning agents
- SQLite persistence
- knowledge-base retrieval
- human-in-the-loop approval

## Models Used
The project supports both local and cloud model deployment patterns through an OpenAI-compatible interface:

- Local option: `LLM_PROVIDER=local`
  - default base URL: `http://localhost:11434/v1`
  - default local model: `llama3.2`
- Cloud option: `LLM_PROVIDER=cloud`
  - default base URL: `https://ollama.com/v1`
  - default cloud model: `gpt-oss:20b`

This design allows the same incident workflow to work with either a local Ollama setup or a hosted cloud endpoint, without changing the application logic.

## Deployment Notes
The original local project remains the working version. A separate deployment-oriented copy was created so the main project stays intact while enabling a deployment-ready setup for a single-process environment.

## Final Summary
This project is a practical AI incident-management assistant designed to help teams investigate issues faster, reduce manual troubleshooting effort, and keep relevant actions grounded in a human-approved process.
