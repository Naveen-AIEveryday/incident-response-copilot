# Incident Response Copilot

An enterprise-grade, AI-assisted IT incident response copilot designed to accelerate incident triage, log analysis, hybrid runbook retrieval, root-cause diagnosis, and post-mortem reporting while strictly enforcing human-in-the-loop operational approval.

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Specialised agents for Triage (`TriageAgent`), Log Analysis (`LogAnalysisAgent`), Runbook Synthesis (`ShortRunbookAgent`), Root Cause Analysis (`RootCauseAgent`), and Post-Mortem Reporting (`ReportAgent`).
- **Pydantic Structured Output Validation**: Strong schema enforcement and automatic JSON normalization with fallback recovery to eliminate LLM parsing crashes.
- **ChromaDB Persistent Vector Store & Hybrid Search**: Combines dense cosine vector similarity with weighted token/phrase sparse matching for exact error code and conceptual runbook matching.
- **Safe Read-Only Diagnostic Commands**: Generates copyable, non-destructive CLI diagnostic commands (e.g. `where.exe python`, `pg_isready`, `ping`, `nslookup`) alongside root-cause findings.
- **Human-in-the-Loop Approval Gate**: Enforces engineer review and sign-off before simulated remediation and post-mortem report generation.
- **High-Concurrency SQLite Storage**: Non-blocking SQLite Write-Ahead Logging (WAL mode) with performance indexing and granular lifecycle audit event tracking.
- **Modern 3-Tab Streamlit UI**:
  - **Tab 1: 🚨 Investigation & Approval**: Quick presets, multi-agent progress trackers, severity metric badges, copyable diagnostic commands, and Markdown report generator.
  - **Tab 2: 📚 Knowledge Base & Runbooks Manager**: Live hybrid search tester, indexed runbooks repository viewer, and dynamic custom runbook ingestion form.
  - **Tab 3: 📊 Incident History & Audit Trail**: Status/keyword filtering and chronological audit event timeline viewer.
- **Comprehensive Automated Test Suite**: 12/12 passing unit and integration tests across agents, knowledge retrieval, database operations, and REST routes.

---

## 🏗️ Project Structure

```text
incident-response-copilot/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Pydantic request/response & agent output schemas
│   ├── agents.py            # Multi-agent definitions, prompts, telemetry, and validation
│   ├── orchestrator.py      # Multi-stage incident investigation workflow
│   ├── knowledge_base.py    # ChromaDB persistent vector store & hybrid search engine
│   ├── database.py          # SQLite persistence with WAL mode & audit event tracking
│   ├── plugins.py           # Semantic Kernel knowledge retrieval plugin
│   ├── routes.py            # REST API route handlers
│   └── config.py            # Environment configuration & port resolution
├── ui/
│   └── streamlit_app.py     # 3-tab interactive Streamlit web interface
├── data/
│   ├── chroma/              # Persistent ChromaDB vector index
│   └── incidents.db         # SQLite incident database & audit log
├── tests/
│   ├── test_agents.py       # Agent JSON parsing, validation, and telemetry tests
│   └── test_orchestrator.py # Database, ChromaDB hybrid search, and API route tests
├── hf_deploy/               # Standalone single-process deployment package
├── run_app.py               # Local concurrent launcher (FastAPI + Streamlit)
├── CAPSTONE_REPORT.md       # Full formal Capstone Project Report
├── Example incidents.txt    # Sample incident presets for manual testing
└── requirements.txt         # Project dependencies
```

---

## ⚡ Quick Start

### 1. Launch the Application
From the project root in PowerShell:

```powershell
& .venv\Scripts\python.exe run_app.py
```

This concurrently starts:
- **FastAPI REST API**: `http://127.0.0.1:9002`
- **Streamlit Web UI**: `http://127.0.0.1:8502`
- **Interactive Swagger Docs**: `http://127.0.0.1:9002/docs`

---

## 🧪 Running Tests

Execute the full automated test suite:

```powershell
& .venv\Scripts\python.exe -m pytest tests/ -v
```

All 12 tests across agent validation, hybrid search, database operations, and API routes will execute.

---

## 🌐 REST API Endpoints

### Incidents
- `POST /incidents` — Submit an incident for multi-agent investigation.
- `GET /incidents` — List past incidents with optional `status`, `search`, and `limit` query filters.
- `GET /incidents/{incident_id}` — Retrieve details and investigation results for a specific incident.
- `DELETE /incidents/{incident_id}` — Delete an incident record and its associated audit trail.
- `GET /incidents/{incident_id}/audit` — Retrieve the chronological audit event log for an incident.
- `POST /incidents/approval` — Submit engineer approval or rejection for remediation.
- `POST /incidents/{incident_id}/report` — Generate an official Markdown post-mortem report.

### Knowledge Base & Runbooks
- `GET /knowledge/runbooks` — List all indexed operational runbooks.
- `POST /knowledge/runbooks` — Ingest a new runbook into ChromaDB.
- `DELETE /knowledge/runbooks/{runbook_id}` — Remove a runbook from the vector database.
- `GET /knowledge/search?q={query}` — Execute hybrid semantic + keyword search across runbooks.

---

## ⚙️ Environment Configuration

Set runtime variables in `.env`:

```ini
# Model Provider: 'cloud' (Ollama Cloud) or 'local' (Local Ollama instance)
LLM_PROVIDER=cloud
OLLAMA_CLOUD_BASE_URL=https://ollama.com/v1
OLLAMA_CLOUD_MODEL=gpt-oss:20b
OLLAMA_API_KEY=your_ollama_api_key_here

# Local Model Fallback
OLLAMA_LOCAL_BASE_URL=http://localhost:11434/v1
OLLAMA_LOCAL_MODEL=llama3.2

# Ports & Storage
API_PORT=9002
STREAMLIT_PORT=8502
SQLITE_PATH=./data/incidents.db
CHROMA_PATH=./data/chroma
```

---

## 🛡️ Safety Architecture

1. **Read-Only Diagnostics**: Suggested commands are strictly informational (e.g. `where.exe python`, `netstat`, `ping`, `nslookup`) to prevent unintended state changes.
2. **Approval Enforcement**: System enforces a hard pause at `pending_human_approval` before generating post-mortem documentation or finalizing incident status.
3. **No Automatic Writes**: No automated shell scripts or modification commands are executed against production servers.

