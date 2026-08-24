# AI-Powered Agentic Incident Response Copilot
An autonomous multi-agent system for automated incident triage, log analysis, hybrid runbook retrieval, root-cause diagnosis, and human-in-the-loop remediation approval. Naveen U, August 2026, Agentic AI developer.

## 1. Executive Summary
The Incident Response Copilot is an AI-powered multi-agent investigation system designed to accelerate the early stages of IT and cloud incident response while preserving operational safety through human approval gates. Built for Site Reliability Engineers (SREs), DevOps teams, and IT operations analysts, the platform processes unstructured incident titles, descriptions, and error logs. It orchestrates specialized agents to perform concurrent triage and log pattern extraction, dense and sparse hybrid runbook retrieval from ChromaDB, short runbook synthesis, and root-cause determination with safe diagnostic CLI commands. The three most significant findings from this project are: (1) partitioning monolithic prompts into specialized, strongly-typed Pydantic agents eliminates schema hallucinations and output variability; (2) combining vector embeddings with token-level keyword matching delivers significantly higher runbook retrieval accuracy for specific error codes (such as HTTP 500 or DNS NXDOMAIN) than semantic vector search alone; and (3) enforcing a strict human-in-the-loop approval gate ensures safe operational oversight before any simulated remediation or post-mortem reporting occurs.

## 2. Problem and Users
Modern cloud and IT infrastructure outages generate voluminous, noisy, and unstructured diagnostic data across heterogeneous log streams, error traces, and user tickets. On-call engineers, SREs, and IT support teams face severe cognitive fatigue during critical production incidents. In these high-pressure scenarios, Mean Time to Resolution (MTTR) is lengthened by manual log parsing, searching through fragmented documentation repositories, and attempting to isolate root causes under tight time constraints. Responders often make inconsistent triage assessments or apply outdated runbooks due to human oversight.

A deterministic script or standard rule-based parser is fundamentally insufficient in this operational environment. Incident descriptions are natural language narratives with varying terminology, error logs contain non-deterministic stack traces across diverse technology stacks, and incident diagnosis requires contextual reasoning to synthesize evidence across disparate sources. Rule engines cannot infer that an HTTP 500 error containing a database timeout correlates to connection pool starvation without an explicit hard-coded rule for every possible permutation. Conversely, an agentic multi-agent architecture utilizes Large Language Models equipped with domain tools, structured schemas, and dynamic vector memory to reason through ambiguous symptoms, identify underlying failure mechanisms, extract evidence, and formulate diagnostic steps adaptively, while remaining safely constrained by human oversight.

## 3. Scope
**In scope**:
- Automated incident severity classification and impact triage from natural language input.
- SRE log analysis, error extraction, pattern detection, and evidence isolation.
- Hybrid semantic vector and keyword runbook retrieval from a persistent ChromaDB vector collection.
- Incident-specific short runbook generation and root-cause synthesis with safe read-only CLI diagnostic commands.
- Human-in-the-loop approval workflow for remediation decisions.
- Automated Markdown post-mortem incident report generation.
- Non-blocking SQLite persistence with audit event lifecycle tracking and a 3-tab Streamlit user interface.

**Out of scope**:
- Autonomous, unapproved execution of write or modification actions on live production infrastructure.
- Ingestion of live distributed telemetry streams (OpenTelemetry, Prometheus, Datadog).
- Multi-tenant enterprise identity management and Role-Based Access Control (RBAC).
- Automatic code patching or Git pull-request generation.

## 4. Architecture
```mermaid
flowchart TD
    User([Operations Engineer]) -->|1. Submits Incident Form| UI[Streamlit User Interface]
    UI -->|2. POST /incidents| FastAPIServer[FastAPI REST Backend]
    FastAPIServer -->|3. Dispatches Request| Orch[Incident Orchestrator]
    Orch -->|4. Writes Initial Record & Audit Event| DB[(SQLite Database WAL Mode)]
    
    subgraph Parallel Stage 1: Triage & Log Analysis
        Orch -->|5a. Async Call| TriageAgent[Triage Specialist Agent]
        Orch -->|5b. Async Call| LogAgent[Log Analysis SRE Agent]
        TriageAgent -->|6a. Validated TriageOutput JSON| Orch
        LogAgent -->|6b. Validated LogAnalysisOutput JSON| Orch
    end

    subgraph Stage 2: Hybrid Retrieval
        Orch -->|7. Semantic + Keyword Query| SKPlugin[Semantic Kernel Knowledge Plugin]
        SKPlugin -->|8. Dense Vector & Sparse Search| ChromaDBStore[(ChromaDB Persistent Vector Store)]
        ChromaDBStore -->|9. Top Ranked Runbooks| SKPlugin
        SKPlugin -->|10. Formatted KB Matches| Orch
    end

    subgraph Stage 3 & 4: Synthesis & Diagnosis
        Orch -->|11. Dispatches Context| RunbookAgent[Short Runbook Specialist Agent]
        RunbookAgent -->|12. Validated ShortRunbookOutput JSON| Orch
        Orch -->|13. Dispatches Evidence & Runbook| RootCauseAgent[Root Cause Commander Agent]
        RootCauseAgent -->|14. Validated RootCauseOutput JSON & CLI Commands| Orch
    end

    Orch -->|15. Updates Status: pending_human_approval| DB
    Orch -->|16. Returns Investigation Payload| FastAPIServer
    FastAPIServer -->|17. Displays Results & Diagnostic Commands| UI
    
    subgraph Human Approval Gate
        User -->|18. Submits Decision & Sign-off| UI
        UI -->|19. POST /incidents/approval| FastAPIServer
        FastAPIServer -->|20. Records Decision & Status Change| Orch
        Orch -->|21. Logs human_approval Event| DB
    end

    subgraph Post-Mortem Reporting
        User -->|22. Requests Final Report| UI
        UI -->|23. POST /incidents/{id}/report| FastAPIServer
        FastAPIServer -->|24. Triggers Report Generation| Orch
        Orch -->|25. Formats Summary & Evidence| ReportAgent[Post-Mortem Reporting Agent]
        ReportAgent -->|26. Returns Markdown Incident Report| Orch
        Orch -->|27. Stores Report & Audit Trail| DB
        Orch -->|28. Renders Report| UI
    end
```

A single incident investigation proceeds through the following numbered end-to-end workflow:
1. **Incident Submission**: The operations engineer inputs the incident title, description, and raw logs in the Streamlit UI, which submits an `IncidentRequest` payload to the FastAPI backend at `POST /incidents`.
2. **Initialization and Persistence**: The FastAPI route invokes the `Orchestrator`, which generates a unique UUID, creates an incident record in SQLite with status `investigating`, and records an initial `incident_created` audit event.
3. **Concurrent Triage and Log Analysis**: The `Orchestrator` uses `asyncio.gather` to concurrently execute the `Triage Specialist Agent` and the `Log Analysis SRE Agent`. The triage agent evaluates severity, affected service, and preliminary investigation steps, while the log analysis agent parses stack traces for key errors, failure patterns, and concrete evidence snippets. Both outputs are parsed and validated against strict Pydantic schemas.
4. **Hybrid Runbook Retrieval**: The orchestrator aggregates the incident description, triage summary, and log findings into a unified search query passed to the `Semantic Kernel Knowledge Plugin`. The plugin performs a hybrid search across the ChromaDB persistent vector collection, combining dense cosine vector similarity with weighted sparse keyword matching to retrieve the top matching operational runbooks.
5. **Short Runbook Generation**: The `Short Runbook Specialist Agent` ingests the incident symptoms and retrieved runbook documentation to generate a focused 3-step recovery procedure tailored specifically to the incident.
6. **Root Cause Analysis and Diagnostic Generation**: The `Root Cause Commander Agent` synthesizes all gathered evidence, determines a probable root cause, assigns a confidence score (0–100%), recommends a safe remediation strategy, and generates safe, read-only CLI diagnostic commands (such as `where.exe python`, `ping`, or connection checks).
7. **Human Approval Gate**: The orchestrator saves the complete investigation payload to SQLite and transitions the incident status to `pending_human_approval`. The engineer reviews the findings, logs, runbook, and diagnostic commands in the Streamlit UI, submitting an explicit Approve or Reject decision with comments.
8. **Post-Mortem Reporting**: Upon approval, the engineer requests a formal post-mortem report. The `Post-Mortem Reporting Agent` compiles the timeline, triage metrics, diagnostic commands, and human sign-off into a standardized Markdown incident report stored in SQLite and displayed in the UI.

## 5. Agent Design
| Agent name | Role | Tools it may call | When it hands off | How it terminates |
|---|---|---|---|---|
| TriageAgent | Classifies incident severity, affected service, and initial steps | OpenAIChatClient | Hands off structured triage JSON to Orchestrator after initial analysis | Returns a validated `TriageOutput` Pydantic model (`severity`, `affected_service`, `incident_summary`, `initial_investigation_steps`) |
| LogAnalysisAgent | Extracts error strings, failure patterns, suspected components, and evidence | OpenAIChatClient | Hands off log analysis JSON to Orchestrator for knowledge retrieval and root-cause analysis | Returns a validated `LogAnalysisOutput` Pydantic model (`key_errors`, `patterns`, `suspected_components`, `evidence`) |
| ShortRunbookAgent | Generates a 3-step actionable recovery procedure tailored to incident symptoms | OpenAIChatClient | Hands off concise runbook JSON to Orchestrator and Root Cause Agent | Returns a validated `ShortRunbookOutput` Pydantic model (`title`, `summary`, `steps`) |
| RootCauseAgent | Synthesizes evidence to diagnose root cause, compute confidence, and suggest read-only CLI commands | OpenAIChatClient | Hands off root-cause diagnosis to Orchestrator to await human approval | Returns a validated `RootCauseOutput` Pydantic model (`root_cause`, `confidence`, `evidence`, `recommended_remediation`, `suggested_commands`, `requires_human_approval`) |
| ReportAgent | Formulates a comprehensive post-mortem Markdown report | OpenAIChatClient | Hands off completed Markdown document to Orchestrator for persistence and UI display | Returns formatted Markdown document containing executive summary, root cause, diagnostic verification, and approval notes |

The multi-agent design is structured around functional specialization and contract enforcement. Rather than relying on a single monolithic prompt, each agent is constrained to a singular domain of responsibility with an explicit prompt contract and a corresponding Pydantic output model. This architectural separation prevents attention dilution, reduces token context per call, and enables concurrent execution between the triage and log analysis stages.

To guarantee system resilience across varying model backends (including local Ollama instances), all agent responses pass through a central validation layer (`parse_and_validate`). This layer strips Markdown code blocks, cleans trailing commas via regex normalization, and validates the dictionary against target Pydantic schemas. If a local model returns malformed JSON, the layer applies default fallback structures rather than terminating the workflow with an unhandled exception. Crucially, the agents operate under strict safety boundaries: the `RootCauseAgent` is prohibited from executing remediation commands autonomously, and the `ShortRunbookAgent` is restricted to non-destructive verification actions.

## 6. Data and Knowledge
The knowledge and operational data architecture consists of two primary tiers:
1. **Persistent ChromaDB Vector Store**: Managed through ChromaDB's `PersistentClient` located at `./data/chroma` with cosine distance space (`hnsw:space: cosine`). The knowledge base contains 10 curated operational documents (9 operational runbooks and 1 historical incident case study, totaling ~15 KB). Topics span database connection pool exhaustion, deployment rollbacks, Windows Python PATH and VS Code interpreter configuration, high CPU saturation, memory leaks (OOMKilled), authentication failures, and Chrome DNS resolution failures. Each document includes metadata tags and document classifications (`runbook`, `historical_incident`, `standard_operating_procedure`).
2. **Hybrid Retrieval Pipeline**: When an incident is investigated, the system constructs a search query combining the incident title, description, raw logs, triage summary, and extracted log evidence. The `KnowledgeBase` executes a hybrid search: ChromaDB dense vector retrieval computes semantic similarity scores, while a tokenized sparse matching algorithm scores keyword presence and exact domain phrases (`HTTP 500`, `NXDOMAIN`, `connection pool exhausted`). The top 2–3 matching runbooks (typically 1–2 KB total) are dynamically injected into downstream prompts.
3. **SQLite Audit and Incident Store**: Stored in `./data/incidents.db` with SQLite Write-Ahead Logging (WAL mode) and performance indexes on `created_at`, `status`, and `incident_id`. The database maintains two relational tables: `incidents` (storing incident metadata, status, and complete JSON investigation payloads) and `audit_events` (storing discrete lifecycle events from `incident_created` to `human_approval` and `report_generated`).

Static system prompts are kept compact, containing only agent instructions and output schemas (approx. 200–350 tokens per agent). All incident details, logs, retrieved runbooks, and intermediate outputs are dynamically injected at runtime.

## 7. Implementation
**Technology Stack & Models**:
- **Backend & REST API**: FastAPI 0.115+, Python 3.11+, Uvicorn
- **Agent Orchestration**: Microsoft Agent Framework (`agent_framework`), Semantic Kernel (`semantic_kernel`), OpenAI-compatible chat client supporting Ollama Cloud (`gpt-oss:20b`) and Ollama Local (`llama3.2`)
- **Vector Database**: ChromaDB 0.6+ (`PersistentClient`)
- **Relational Persistence**: SQLite 3 with WAL journal mode
- **Frontend UI**: Streamlit 1.40+ (Multi-tab layout with interactive session state)
- **Validation & Test Harness**: Pydantic v2, Pytest 9.1+

**Three Most Significant Technical Decisions**:
1. **Pydantic Schema Validation with Fallback Normalization vs. Raw String Prompts**:
   - *Decision*: Enforced strict Pydantic models for every agent response and implemented an LLM JSON normalizer (`_normalize_llm_json`) with default fallbacks.
   - *Rejected Alternative*: Unstructured string parsing or raw `json.loads`. Rejected because local and cloud LLMs occasionally output Markdown fences, trailing commas, or incomplete brackets, which caused runtime crashes in downstream services.
2. **Dense and Sparse Hybrid Runbook Search vs. Pure Vector Cosine Search**:
   - *Decision*: Combined ChromaDB vector similarity with weighted token/phrase keyword matching.
   - *Rejected Alternative*: Pure vector embedding similarity. Rejected because vector embeddings frequently fail to match exact alphanumeric error codes and environment tokens (such as `500`, `503`, `ERR_CONNECTION_TIMED_OUT`, `where.exe`) that are critical in IT incident response.
3. **Human-in-the-Loop Approval Gate vs. Fully Autonomous Execution**:
   - *Decision*: System pauses at `pending_human_approval`, providing safe read-only CLI diagnostic commands and requiring an engineer's sign-off before generating the final report.
   - *Rejected Alternative*: Autonomous automated remediation execution. Rejected because executing remediation scripts without human verification carries severe operational risk of cascading production outages or unintended data modification.

## 8. Evaluation
The project was evaluated through an automated test suite, structural regression validation, and manual scenario verification:
1. **Automated Pytest Suite (`tests/test_agents.py`, `tests/test_orchestrator.py`)**:
   - **Dataset Size & Cases**: 12 discrete automated test cases covering agent response parsing, Pydantic validation, telemetry calculations, database CRUD/WAL concurrency, ChromaDB hybrid search, and FastAPI REST endpoints.
   - **Case Creation**: Test cases were constructed using synthetic incident payloads and raw LLM response fixtures representing edge cases (e.g., JSON responses with explanatory lead-in text, trailing commas, missing keys, and invalid non-object JSON).
   - **Test Slices**:
     - *Agent Parsing & Schema Slice*: Verifies `TriageOutput`, `LogAnalysisOutput`, `ShortRunbookOutput`, and `RootCauseOutput` validation, including extraction of `suggested_commands` and fallback recovery on corrupt outputs.
     - *Telemetry Slice*: Verifies calculation of TTFT, total latency, character counts, and context usage percentage.
     - *Knowledge Base & Hybrid Search Slice*: Verifies ChromaDB persistence, cosine similarity scoring, keyword token boosts, dynamic runbook addition, and deletion.
     - *Database & Concurrency Slice*: Verifies SQLite WAL mode operations, status updates, filtered search queries, and audit event insertion.
     - *API Route Slice*: Verifies FastAPI endpoints (`GET /`, `GET /incidents`, `POST /incidents`, `POST /knowledge/runbooks`, `GET /knowledge/search`, `DELETE /knowledge/runbooks/{id}`) using `fastapi.testclient.TestClient`.
   - **Scoring Method**: Deterministic code checks and assertion verification. Each test case was executed once per test suite run.
2. **End-to-End Scenario Verification**:
   - Evaluated across three real-world scenario presets: (1) Windows Python PATH and VS Code interpreter misconfiguration, (2) Database connection pool exhaustion with HTTP 500 error spikes, and (3) Chrome network timeout with DNS NXDOMAIN failure.
   - **Scoring Method**: Manual human evaluation of triage accuracy, runbook relevance, and post-mortem report clarity. The number of repeated end-to-end runs per scenario was not measured.

## 9. Results
| Test / Metric Category | Measured Value | Verification Method | Status / Notes |
|---|---|---|---|
| Automated Pytest Test Suite | 12 passed / 12 total (100%) | Code check (`pytest tests/ -v`) | Completed in 8.49s with zero failures |
| Agent Schema Validation Pass Rate | 100% on tested fixtures | Code check (Pydantic v2) | Successfully validates structured JSON and falls back gracefully |
| ChromaDB Hybrid Runbook Retrieval | 100% top-rank accuracy on test queries | Code check (`temp_kb.search()`) | Correctly retrieves exact matches for DB Pool, Redis, and Python runbooks |
| Database Concurrency & Search | 100% passing | Code check (SQLite WAL Mode) | Filtered queries, audit logging, and incident deletion verified |
| FastAPI REST API Endpoints | 100% passing (HTTP 200) | Code check (`TestClient`) | All CRUD and investigation routes verified |
| Total Latency (Local `llama3.2`) | not measured | Telemetry tracking enabled | Displays in UI per agent call; aggregate benchmark not measured |
| Total Latency (Cloud `gpt-oss:20b`) | not measured | Telemetry tracking enabled | Displays in UI per agent call; aggregate benchmark not measured |
| Time to First Token (TTFT) | not measured | Non-streaming estimate enabled | Estimated at 75% total latency in non-streaming mode |
| Token Cost per Incident Request | not measured | Cloud provider billing | Direct token-cost accounting not implemented |
| User MTTR Reduction (%) | not measured | Human user study | Requires production deployment trial; not measured |
| Human Evaluation Score (CSAT / Likert) | not measured | Engineer survey | Formal user study not conducted; not measured |

The project demonstrates complete structural correctness, schema compliance, vector persistence, and functional reliability across its 12 automated unit and integration tests. The FastAPI backend, multi-agent orchestration pipeline, and Streamlit user interface operate reliably without runtime crashes.

**Identified Gaps & Future Work**:
- *Benchmark Dataset Size*: A standardized, large-scale multi-class incident benchmark dataset was not measured or evaluated.
- *Quantitative Cost Tracking*: Token consumption and dollar cost per incident investigation were not measured.
- *End-to-End Latency Benchmarking*: Comprehensive multi-run latency statistics across varied hardware profiles were not measured.
- *Formal Human Evaluation*: Longitudinal Mean Time to Resolution (MTTR) reduction and human engineering satisfaction scores were not measured.
