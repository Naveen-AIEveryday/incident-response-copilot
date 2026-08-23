import re
from typing import Any


class KnowledgeBase:
    def __init__(self):
        self.documents = [
            {
                "title": "Database Connection Pool Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Deployment Rollback Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Python Environment Setup Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "VS Code Python Interpreter Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Python PATH Troubleshooting Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "High CPU Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Memory Usage Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Authentication Failure Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Chrome Website Loading Runbook",
                "document_type": "runbook",
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
                """,
            },
            {
                "title": "Historical Payment API Incident",
                "document_type": "historical_incident",
                "content": """
A payment API incident was caused by database connection pool exhaustion.
The issue started after a retry feature deployment.
The team rolled back the deployment after human approval.
                """,
            },
        ]

    def search(
        self,
        query: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        query_text = query.lower()
        query_text = query_text.replace("-", " ")
        query_text = query_text.replace("_", " ")

        query_words = {
            token
            for token in re.findall(r"[a-z0-9]+", query_text)
            if len(token) > 2
        }

        query_phrases = [
            "python is not recognized",
            "python command",
            "vs code",
            "visual studio code",
            "python interpreter",
            "path environment variable",
            "not recognized",
            "virtual environment",
            "python path",
            "website is not loading",
            "website not loading",
            "google chrome",
            "chrome",
            "blank page",
            "dns",
            "err connection timed out",
            "connection timed out",
            "page could not be reached",
            "loading spinner",
            "not loading",
            "database connection pool",
            "connection pool exhausted",
            "database timeout",
            "http 500",
            "backend 500",
            "deployment rollback",
            "after deployment",
            "error started after deployment",
            "retry feature deployment",
            "payment api",
            "high cpu",
            "memory usage",
            "authentication failure",
            "401",
            "token configuration",
            "identity provider",
        ]

        scored_documents = []

        for document in self.documents:
            if document.get("document_type") != "runbook":
                continue

            title = document["title"].lower()
            content = document["content"].lower()
            text = f"{title}\n{content}"

            score = 0

            for phrase in query_phrases:
                if phrase in text:
                    score += 8

            for word in query_words:
                if len(word) <= 2:
                    continue

                if word in title:
                    score += 6

                if word in content:
                    score += 2

            if "python" in query_words and "python" in text:
                score += 3

            if "vscode" in query_words and "vscode" in text:
                score += 3

            if "interpreter" in query_words and "interpreter" in text:
                score += 3

            if "database" in query_words and "database" in text:
                score += 4

            if "deployment" in query_words and "deployment" in text:
                score += 4

            if "500" in query_words and "500" in text:
                score += 4

            if "chrome" in query_words and "chrome" in text:
                score += 4

            if score >= 4:
                scored_documents.append(
                    (score, document)
                )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            {
                **document,
                "score": score,
            }
            for score, document in scored_documents[:limit]
        ]

    def add_document(
        self,
        title: str,
        content: str,
        document_type: str,
    ) -> None:
        self.documents.append(
            {
                "title": title,
                "content": content,
                "document_type": document_type,
            }
        )