# High-Level Project Report: Incident Response Copilot

## 1. Project Purpose
The Incident Response Copilot is an AI-powered multi-agent investigation system engineered to accelerate the initial phases of IT incident response, root-cause diagnosis, and post-mortem reporting while preserving operational safety through human approval gates.

## 2. Core Capabilities
When an engineer inputs an incident title, narrative description, and raw error logs, the system orchestrates a multi-stage workflow:
1. **Parallel Triage & SRE Log Analysis**: Concurrently classifies severity (`low`, `medium`, `high`, `critical`), identifies impacted services, and extracts error traces and anomalies.
2. **Persistent Hybrid Knowledge Retrieval**: Queries a ChromaDB vector database using cosine semantic similarity combined with token/phrase keyword matching to match exact error codes and conceptual runbooks.
3. **Short Actionable Runbook Synthesis**: Generates a 3-step actionable recovery procedure tailored specifically to the incident symptoms.
4. **Root Cause Analysis & Safe Diagnostic Commands**: Synthesizes all gathered evidence, evaluates confidence (0–100%), determines the root cause, and provides safe, read-only CLI diagnostic commands (e.g. `where.exe python`, `pg_isready`, `ping`, `nslookup`).
5. **Human Approval Gate**: Holds execution at `pending_human_approval` to require engineer sign-off and comments.
6. **Standardized Post-Mortem Report**: Compiles an official Markdown post-mortem incident report upon approval.

## 3. Key Architecture & Modules
- **`app/agents.py`**: Multi-agent definitions (`TriageAgent`, `LogAnalysisAgent`, `ShortRunbookAgent`, `RootCauseAgent`, `ReportAgent`), telemetry tracking, and Pydantic validation with `parse_and_validate()`.
- **`app/models.py`**: Strict Pydantic schemas enforcing input contracts and agent output integrity.
- **`app/knowledge_base.py`**: ChromaDB persistent vector collection (`./data/chroma`) and hybrid dense/sparse search engine.
- **`app/database.py`**: SQLite database configured in Write-Ahead Logging (WAL) mode with performance indexes on `created_at`, `status`, and `incident_id`.
- **`app/orchestrator.py`**: Multi-stage event-driven investigation coordinator.
- **`app/routes.py`**: REST API exposing incident CRUD, search filtering, runbook ingestion/deletion, and audit history.
- **`ui/streamlit_app.py`**: Modern 3-tab user interface (Investigation & Approval, Knowledge Base Manager, Incident History Explorer).

## 4. Verification & Testing
- **12/12 passing unit and integration tests** in `tests/test_agents.py` and `tests/test_orchestrator.py`.
- Covers Pydantic schema validation, LLM JSON normalization, telemetry calculations, ChromaDB hybrid search, database WAL concurrency, and FastAPI REST endpoints.

## 5. Summary & Safety Guarantee
The copilot ensures complete operational safety by operating as an assistive diagnostic copilot rather than an autonomous actuator: all suggested diagnostic CLI commands are strictly read-only, and no automated changes are executed against production environments without human approval.

