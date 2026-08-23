# AI-powered Incident Response Copilot for triaging incidents, generating runbooks, and enforcing human approval — Naveenkumar Ugargol, 2026-08-23, Agentic AI Developer

## 1. Executive Summary
This project is an AI-assisted incident response tool designed for technical teams that need a fast, structured way to investigate incidents without jumping directly into unsafe remediation. A user submits an incident title, description, and logs, and the system triages the issue, identifies likely failure patterns, retrieves relevant runbooks, creates a short action plan, and suggests a probable root cause before requiring a human approval step. The system is aimed primarily at IT operations, support engineers, and developers who need a faster first-pass investigation workflow. The most important finding is that the design works as a multi-agent workflow rather than a single script: different agents specialize in separate tasks, which makes the output more structured and easier to review. A second key finding is that the project relies on a knowledge-base layer for contextual grounding, which reduces hallucination risk and keeps the generated runbook brief and relevant. The final important finding is that the workflow is intentionally human-in-the-loop, so it does not execute remediation automatically.

## 2. Problem and Users
Modern incident response often begins with incomplete or noisy information. Engineers receive alerts, logs, and partial descriptions, but the first few steps are still manual: triage, log review, runbook lookup, and root-cause narrowing. This is slow, error-prone, and often becomes inconsistent across teams. The project addresses that by providing a structured workflow that turns a rough incident description into a cleaner triage summary, a log-analysis view, a relevant runbook, and a root-cause recommendation. The intended users are IT operations teams, support engineers, site reliability engineers, and developers handling production incidents. This tool is especially valuable when a person needs a quick first-pass analysis before escalating to a broader incident response process. A plain script would not be enough because the workflow needs context-aware reasoning, multiple specialized prompts, knowledge retrieval, and human approval. The challenge is not only generating text but also coordinating evidence, structure, and workflow control in a way that is consistent and reviewable.

## 3. Scope
- In scope
  - Incident triage from user-provided title, description, and logs
  - Log pattern extraction and evidence gathering
  - Knowledge-base runbook matching for likely troubleshooting paths
  - Short incident-specific runbook generation
  - Root-cause analysis with evidence and confidence
  - Human approval step before simulated remediation completion
  - Final Markdown report generation
  - Local FastAPI + Streamlit workflow and a separate deployment-oriented copy
- Out of scope
  - Real production remediation execution
  - Full service monitoring, alerting, or telemetry ingestion
  - Enterprise authentication or user management
  - Real-time distributed tracing or metric correlation
  - Production-grade RBAC, audit governance, or multi-tenant deployment
  - Full benchmark dataset creation or large-scale evaluation pipeline

## 4. Architecture
```mermaid
flowchart LR
    A[Streamlit UI] --> B[FastAPI /incidents endpoint]
    B --> C[Incident Orchestrator]
    C --> D[Triage Agent]
    C --> E[Log Analysis Agent]
    C --> F[Knowledge Base Search]
    D --> G[Short Runbook Agent]
    E --> G
    F --> G
    G --> H[Root Cause Agent]
    H --> I[Human Approver]
    I --> J[SQLite Incident Store]
    H --> K[Markdown Report]
    J --> L[Incident history and audit events]
```

A single request begins when a user enters an incident in the Streamlit UI. The app posts the incident to the FastAPI API at /incidents. The FastAPI route calls the Orchestrator, which creates an incident record in SQLite and logs the event. The Orchestrator then runs the Triage Agent and the Log Analysis Agent in parallel, because they operate on the same incident input but answer different questions. The Triage Agent classifies severity, service impact, and initial steps; the Log Analysis Agent extracts likely error patterns and evidence. Once those are produced, the Orchestrator builds a rich search query and calls the knowledge-base search component. That component filters a built-in runbook list to the most relevant entries, using keywords and symptom matching rather than a heavy external vector index. The Short Runbook Agent takes the incident details, triage output, and relevant knowledge to produce a brief and actionable runbook. The Root Cause Agent then synthesizes the evidence from the incident, logs, runbook, and prior output to propose the most likely cause and remediation. The workflow deliberately stops at a human approval step rather than executing remediation automatically. The resulting investigation data, approval record, and report are stored in SQLite and can be retrieved later through the API or UI.

## 5. Agent Design
| Agent name | Role | Tools it may call | When it hands off | How it terminates |
|---|---|---|---|---|
| TriageAgent | Classifies severity, service impact, and initial investigation steps | OpenAI-compatible chat client | Passes structured triage output to orchestrator and downstream summarization | Returns a JSON object with severity, affected_service, incident_summary, and initial_investigation_steps |
| LogAnalysisAgent | Extracts key errors, patterns, and suspected components | OpenAI-compatible chat client | Passes results to root-cause and short-runbook stages | Returns a JSON object with key_errors, patterns, suspected_components, and evidence |
| RootCauseAgent | Produces the most likely cause and a safe remediation recommendation | OpenAI-compatible chat client; knowledge context passed in prompt | Passes final root cause analysis to the orchestrator and report pipeline | Returns a JSON object with root_cause, confidence, evidence, recommended_remediation, and requires_human_approval |
| ShortRunbookAgent | Produces a concise, incident-specific action plan | OpenAI-compatible chat client; knowledge context passed in prompt | Hands off to the orchestrator and then root-cause analysis | Returns JSON with title, summary, and up to three steps |
| ReportAgent | Converts the investigation into a final Markdown incident report | OpenAI-compatible chat client | Produces final report for the UI and storage | Returns plain Markdown text |

The agent design emphasizes specialization rather than monolithic prompting. Each agent has a single responsibility and a sharply defined JSON schema, which reduces ambiguity and makes downstream logic easier to validate. The system also limits prompt size by passing only a narrow slice of knowledge-based context, which is important for local-model reliability and lower token cost. A second design decision is to keep the workflow human-in-the-loop: even when the model returns a likely remediation, the orchestrator does not execute it; it records the recommendation and waits for approval. The final design decision is response normalization. Because the model output can include explanatory text or trailing commas, the project includes JSON parsing logic to recover valid structured output. This is an important robustness feature for model variability.

## 6. Data and Knowledge
The application uses two important data paths. First, it stores incidents and audit events in SQLite through app/database.py. Each incident record includes the incident ID, title, description, logs, status, timestamp, and JSON payload of investigation results. The audit_events table stores event history for each incident, so a reviewer can trace what happened from creation through approval. Second, the project contains a built-in knowledge base in app/knowledge_base.py. This file includes ten records: nine runbooks and one historical incident example. The knowledge entries are static, hand-written documents rather than a large external dataset or vector store. The project also includes a Chroma data directory, but the active retrieval flow in the current implementation is driven by the built-in Python knowledge list and a keyword-based search function, not by a fully prepared external vector index. In other words, the prompt carries the current incident details and a short slice of relevant KB context, while the run-time retrieval happens on-demand from the built-in knowledge list. This is a lightweight design and is appropriate for a capstone project because it keeps the system understandable and inspectable.

## 7. Implementation
The stack is Python-based and uses FastAPI for the backend, Streamlit for the frontend, SQLite for persistence, and an OpenAI-compatible chat client from the agent framework for model access. The project supports both local and cloud modes through app/config.py, using environment variables for selection. The main model configuration supports a local Ollama endpoint with llama3.2 and a cloud-compatible Ollama endpoint with gpt-oss:20b. The three most important technical decisions were: first, using a multi-agent workflow with a strict JSON contract for each stage; second, keeping retrieval narrowly scoped to a short list of likely runbooks to avoid overloaded prompts; and third, separating the local working project from a deployment-oriented copy in hf_deploy so the original app remains intact while a single-process deployment path can be prepared. The main rejected alternative was a monolithic single prompt that tried to do triage, log analysis, runbook retrieval, root cause, and report generation in one pass. That was rejected because it was harder to validate, less structured, and less reliable for prompt-length management. Another rejected option was assuming local-only model access throughout the project; this was replaced with provider-aware config because a cloud-compatible endpoint is more portable and matches deployment requirements.

## 8. Evaluation
The project contains a small focused test suite in tests/test_agents.py, but it is not a production-scale incident dataset and it does not evaluate real incident quality across a large set of cases. The test suite covers JSON parsing robustness, short-runbook generation from an incident and KB match, and backend candidate prioritization. The dataset size is not measured because no external benchmark dataset or curated incident corpus was created or committed. The cases in the repo are synthetic examples used to validate parsing and routing logic, not a statistically representative workload. The evaluation methods are code checks and regression tests, not model-judge scoring or human annotation. Each test case is run once in the current suite; the number of repeated runs per case is not measured. There are no cost, latency, or quality benchmarks recorded for end-to-end incident investigations, so those metrics are not measured. The repository also does not include a dedicated evaluation harness or logged results files beyond the test checks. The practical conclusion is that the project is validated for structural correctness, but not yet benchmarked for real-world accuracy or operational performance.

## 9. Results
| Check | Result | Notes |
|---|---|---|
| Pytest regression suite | 4 passed in 1.99s | Real run from `pytest tests/test_agents.py -q` |
| Local app startup | not measured | No formal startup benchmark recorded |
| End-to-end incident quality | not measured | No labeled incident dataset or human evaluation results |
| Cost per request | not measured | No token/cost tracking implemented |
| Latency per request | not measured | No latency benchmark captured |
| Knowledge retrieval relevance | not measured | No formal retrieval scoring or evaluation script |
| Human approval quality | not measured | No user study or structured approval review |

This project does have a verified structural result: the repository’s focused regression tests pass, and the JSON-parsing and backend-candidate logic are working under the current test set. However, the broader operational metrics that one would usually expect in a capstone evaluation are not measured. The main gaps are dataset coverage, human evaluation, cost analysis, latency analysis, and retrieval-quality scoring. Gaps: dataset size not measured; number of cases run not measured; latency not measured; cost not measured; real-world quality scoring not measured; end-to-end accuracy against production incidents not measured.
