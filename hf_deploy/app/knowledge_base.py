import re
import uuid
from typing import Any

from app.config import CHROMA_PATH

DEFAULT_DOCUMENTS: list[dict[str, Any]] = [
    {
        "id": "doc-db-pool",
        "title": "Database Connection Pool Runbook",
        "document_type": "runbook",
        "tags": ["database", "pool", "timeout", "http-500"],
        "content": """
Symptoms:
- Database connection timeout.
- Connection pool exhausted.
- API returns HTTP 500 errors.

Resolutions:
1. Check database connection pool usage.
2. Check active database connections.
3. Review recent deployments.
4. Increase the connection pool only through approved change management.
5. Restart unhealthy application instances after human approval.
6. Roll back the latest deployment if the issue started after deployment.

Human approval is required before remediation.
        """.strip(),
    },
    {
        "id": "doc-rollback",
        "title": "Deployment Rollback Runbook",
        "document_type": "runbook",
        "tags": ["deployment", "rollback", "http-500", "http-503", "health-check"],
        "content": """
Symptoms:
- Errors begin immediately after a deployment.
- Health checks fail after a new version is released.
- Application returns HTTP 500 or HTTP 503 errors.

Resolutions:
1. Compare deployment time with incident start time.
2. Review application and configuration changes.
3. Check the previous stable version.
4. Request human approval.
5. Roll back to the previous stable version.
6. Monitor the service after rollback.
        """.strip(),
    },
    {
        "id": "doc-py-env",
        "title": "Python Environment Setup Runbook",
        "document_type": "runbook",
        "tags": ["python", "windows", "vscode", "path", "terminal"],
        "content": """
Problem:
Python is installed, but Windows, VS Code, or the terminal cannot identify
the Python command.

Possible causes:
- Python was not added to the PATH environment variable.
- VS Code is using the wrong Python interpreter.
- The Python extension is missing.
- The virtual environment is not activated.
- Windows App Execution Aliases are redirecting python commands.
- The terminal was opened before Python was installed.

Resolutions:
1. Run "py --version" in PowerShell.
2. Run "python --version" in PowerShell.
3. Run "where.exe python" to find the Python executable.
4. Install the Microsoft Python extension in VS Code.
5. Select the interpreter using:
   Command Palette -> Python: Select Interpreter.
6. Select the project's .venv interpreter.
7. Activate the virtual environment:
   .venv\\Scripts\\Activate.ps1
8. Add the Python installation directory to the Windows PATH.
9. Add the Python Scripts directory to the Windows PATH.
10. Restart VS Code after changing PATH.
11. Disable Windows App Execution Aliases for python.exe and python3.exe.
12. Reinstall Python and enable "Add Python.exe to PATH".

Verification:
- python --version
- py --version
- where.exe python
- python -m pip --version
- python -m app.main

Do not change system environment variables automatically.
Request human approval before making operating-system changes.
        """.strip(),
    },
    {
        "id": "doc-vscode-interp",
        "title": "VS Code Python Interpreter Runbook",
        "document_type": "runbook",
        "tags": ["vscode", "interpreter", "venv", "powershell"],
        "content": """
Problem:
Python works in the operating-system terminal but is not recognized inside VS Code.

Resolutions:
1. Install the official Python extension by Microsoft.
2. Open the project folder in VS Code.
3. Press Ctrl+Shift+P.
4. Select Python: Select Interpreter.
5. Select the interpreter inside the project .venv folder.
6. Close and reopen the VS Code terminal.
7. Run:
   python --version
   python -m pip --version
8. If the virtual environment does not exist, run:
   python -m venv .venv
9. Activate it:
   .venv\\Scripts\\Activate.ps1
10. Reload VS Code using Developer: Reload Window.

If PowerShell blocks activation, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
        """.strip(),
    },
    {
        "id": "doc-py-path",
        "title": "Python PATH Troubleshooting Runbook",
        "document_type": "runbook",
        "tags": ["python", "path", "windows", "terminal"],
        "content": """
Problem:
The python command is not recognized on Windows.

Investigation:
1. Run py --version.
2. Run python --version.
3. Run where.exe python.
4. Check whether Python exists in:
   C:\\Users\\<user>\\AppData\\Local\\Programs\\Python
5. Check whether the Python Scripts directory exists.

Resolutions:
1. Restart the terminal.
2. Restart VS Code.
3. Add the Python installation directory to User PATH.
4. Add the Python Scripts directory to User PATH.
5. Disable Python App Execution Aliases.
6. Reinstall Python with Add Python to PATH selected.
7. Use the Python launcher:
   py -m pip install -r requirements.txt
   py -m app.main

Verification:
python --version
py --version
where.exe python
        """.strip(),
    },
    {
        "id": "doc-high-cpu",
        "title": "High CPU Runbook",
        "document_type": "runbook",
        "tags": ["cpu", "performance", "scaling", "hotspot"],
        "content": """
Symptoms:
- CPU usage is above 90 percent.
- Application response time is increasing.
- Worker queues are growing.

Resolutions:
1. Identify the busiest process.
2. Review recent deployments.
3. Check request volume.
4. Check for infinite loops or expensive queries.
5. Scale the application after human approval.
6. Roll back a recent deployment if appropriate.
        """.strip(),
    },
    {
        "id": "doc-memory",
        "title": "Memory Usage Runbook",
        "document_type": "runbook",
        "tags": ["memory", "oom", "leak", "oomkilled"],
        "content": """
Symptoms:
- Memory usage continuously increases.
- Application restarts unexpectedly.
- OutOfMemoryError appears in logs.

Resolutions:
1. Check memory usage by process.
2. Review recent code and configuration changes.
3. Check for a memory leak.
4. Restart an unhealthy application instance after approval.
5. Increase memory allocation through change management.
6. Roll back a recent deployment if it caused the issue.
        """.strip(),
    },
    {
        "id": "doc-auth-fail",
        "title": "Authentication Failure Runbook",
        "document_type": "runbook",
        "tags": ["auth", "401", "identity", "token"],
        "content": """
Symptoms:
- Users cannot log in.
- Authentication requests return HTTP 401.
- Identity-provider requests fail.

Resolutions:
1. Check identity-provider availability.
2. Check token configuration and expiration.
3. Validate application credentials.
4. Check network connectivity.
5. Review recent authentication configuration changes.
6. Roll back a faulty configuration after human approval.
        """.strip(),
    },
    {
        "id": "doc-chrome-loading",
        "title": "Chrome Website Loading Runbook",
        "document_type": "runbook",
        "tags": ["chrome", "dns", "nxdomain", "timeout", "browser", "network"],
        "content": """
Problem:
A website does not load in Google Chrome.
The user sees a blank page, a timeout, or a loading spinner.

Possible causes:
- DNS resolution failure.
- Network connectivity issue.
- Proxy or firewall blocking the site.
- Browser cache or extensions interfering.
- Wrong host or backend service not reachable.
- Site is offline or certificate validation is failing.

Investigation:
1. Check whether the website loads in another browser.
2. Verify the URL and DNS resolution.
3. Run ping or nslookup for the host.
4. Check whether the backend service is reachable.
5. Review browser proxy, firewall, and certificate settings.
6. Disable extensions and clear the browser cache.

Resolutions:
1. Confirm the target host is online and resolvable.
2. Check network connectivity and firewall rules.
3. Clear Chrome cache and cookies for the site.
4. Disable browser extensions that may block content.
5. Verify the site is reachable from a different device or browser.
6. Ask the user to retry after the hostname or certificate issue is fixed.
7. Escalate to network or infrastructure teams if DNS or routing is broken.

Verification:
- browser can load the site successfully
- DNS resolves correctly
- no ERR_CONNECTION_TIMED_OUT or NXDOMAIN errors remain
        """.strip(),
    },
    {
        "id": "doc-hist-payment",
        "title": "Historical Payment API Incident",
        "document_type": "historical_incident",
        "tags": ["payment", "database", "connection-pool", "history"],
        "content": """
A payment API incident was caused by database connection pool exhaustion.
The issue started after a retry feature deployment.
The team rolled back the deployment after human approval.
        """.strip(),
    },
]


class KnowledgeBase:
    def __init__(self, chroma_path: str | None = None):
        self.chroma_path = chroma_path or CHROMA_PATH
        self.documents: list[dict[str, Any]] = [dict(doc) for doc in DEFAULT_DOCUMENTS]
        self.collection = None
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Initialize ChromaDB vector store and seed default documents."""
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = client.get_or_create_collection(
                name="incident_runbooks",
                metadata={"hnsw:space": "cosine"},
            )

            # Seed collection if empty
            if self.collection.count() == 0:
                ids = [doc["id"] for doc in self.documents]
                docs = [f"{doc['title']}\n\n{doc['content']}" for doc in self.documents]
                metadatas = [
                    {
                        "title": doc["title"],
                        "document_type": doc.get("document_type", "runbook"),
                        "tags": ",".join(doc.get("tags", [])),
                    }
                    for doc in self.documents
                ]
                self.collection.add(ids=ids, documents=docs, metadatas=metadatas)
        except Exception:
            # Gracefully operate with keyword fallback if Chroma cannot initialize
            self.collection = None

    def _score_keyword(self, query: str, document: dict[str, Any]) -> float:
        """Calculate weighted keyword/phrase match score."""
        query_text = query.lower().replace("-", " ").replace("_", " ")
        query_words = {
            token for token in re.findall(r"[a-z0-9]+", query_text)
            if len(token) > 2
        }

        query_phrases = [
            "python is not recognized", "python command", "vs code", "visual studio code",
            "python interpreter", "path environment variable", "not recognized",
            "virtual environment", "python path", "website is not loading",
            "website not loading", "google chrome", "chrome", "blank page", "dns",
            "err connection timed out", "connection timed out", "page could not be reached",
            "loading spinner", "not loading", "database connection pool",
            "connection pool exhausted", "database timeout", "http 500", "backend 500",
            "deployment rollback", "after deployment", "error started after deployment",
            "retry feature deployment", "payment api", "high cpu", "memory usage",
            "authentication failure", "401", "token configuration", "identity provider",
            "oomkilled", "outofmemoryerror", "memory leak", "503", "500", "timeout"
        ]

        title = document.get("title", "").lower()
        content = document.get("content", "").lower()
        tags = [t.lower() for t in document.get("tags", [])]
        full_text = f"{title}\n{' '.join(tags)}\n{content}"

        score = 0.0

        for phrase in query_phrases:
            if phrase in query_text and phrase in full_text:
                score += 8.0

        for word in query_words:
            if len(word) <= 2:
                continue
            if word in title:
                score += 8.0
            if word in tags:
                score += 6.0
            if word in content:
                score += 2.0

        # Domain term boosts
        boost_terms = {
            "python": 4.0, "vscode": 4.0, "interpreter": 4.0,
            "database": 4.0, "deployment": 4.0, "500": 4.0,
            "503": 4.0, "chrome": 4.0, "dns": 4.0, "memory": 4.0,
            "cpu": 4.0, "auth": 4.0, "redis": 5.0, "kafka": 5.0
        }
        for term, boost in boost_terms.items():
            if term in query_words and term in full_text:
                score += boost

        return score


    def search(
        self,
        query: str,
        limit: int = 3,
        document_type: str = "runbook",
    ) -> list[dict[str, Any]]:
        """Hybrid search combining ChromaDB semantic similarity with keyword scoring."""
        scores_by_id: dict[str, float] = {}
        docs_by_id: dict[str, dict[str, Any]] = {doc["id"]: doc for doc in self.documents}

        # 1. Semantic vector search via ChromaDB
        if self.collection and self.collection.count() > 0:
            try:
                chroma_results = self.collection.query(
                    query_texts=[query],
                    n_results=min(limit * 3, self.collection.count()),
                )
                if chroma_results and chroma_results.get("ids"):
                    matched_ids = chroma_results["ids"][0]
                    distances = chroma_results.get("distances", [[]])[0] if chroma_results.get("distances") else []

                    for rank, doc_id in enumerate(matched_ids):
                        # Cosine distance: 0 = identical, 2 = opposite
                        dist = distances[rank] if rank < len(distances) else 1.0
                        semantic_score = max(0.0, (1.0 - (dist / 2.0))) * 12.0
                        scores_by_id[doc_id] = scores_by_id.get(doc_id, 0.0) + semantic_score
            except Exception:
                pass

        # 2. Keyword / Token match scoring
        for doc in self.documents:
            doc_id = doc["id"]
            if document_type and doc.get("document_type") != document_type:
                continue

            kw_score = self._score_keyword(query, doc)
            scores_by_id[doc_id] = scores_by_id.get(doc_id, 0.0) + kw_score

        # 3. Filter and rank results
        ranked_results: list[dict[str, Any]] = []
        for doc_id, total_score in scores_by_id.items():
            if total_score >= 3.0:
                doc = docs_by_id.get(doc_id)
                if doc:
                    if document_type and doc.get("document_type") != document_type:
                        continue
                    ranked_results.append({
                        **doc,
                        "score": round(total_score, 2),
                    })

        ranked_results.sort(key=lambda item: item.get("score", 0), reverse=True)
        return ranked_results[:limit]

    def add_document(
        self,
        title: str,
        content: str,
        document_type: str = "runbook",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add a new runbook to the knowledge base and ChromaDB vector collection."""
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        doc = {
            "id": doc_id,
            "title": title.strip(),
            "content": content.strip(),
            "document_type": document_type.strip(),
            "tags": tags or [],
        }
        self.documents.append(doc)

        if self.collection:
            try:
                self.collection.add(
                    ids=[doc_id],
                    documents=[f"{title}\n\n{content}"],
                    metadatas=[{
                        "title": title,
                        "document_type": document_type,
                        "tags": ",".join(tags or []),
                    }],
                )
            except Exception:
                pass

        return doc

    def list_documents(self, document_type: str | None = None) -> list[dict[str, Any]]:
        """List all indexed runbooks and documents."""
        if document_type:
            return [doc for doc in self.documents if doc.get("document_type") == document_type]
        return list(self.documents)

    def delete_document(self, document_id: str) -> bool:
        """Remove a runbook from the in-memory registry and Chroma collection."""
        initial_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.get("id") != document_id]
        deleted = len(self.documents) < initial_count

        if self.collection and deleted:
            try:
                self.collection.delete(ids=[document_id])
            except Exception:
                pass

        return deleted