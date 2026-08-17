from typing import Any

import chromadb

from app.config import CHROMA_PATH


class KnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name="incident_knowledge",
            metadata={
                "description": (
                    "Runbooks and historical incident documents"
                )
            },
        )

        self._seed_documents()

    def _seed_documents(self) -> None:
        if self.collection.count() > 0:
            return

        documents = [
            {
                "id": "runbook-db-pool",
                "title": "Database Connection Pool Exhaustion Runbook",
                "type": "runbook",
                "content": """
Symptoms:
- API error rate increases.
- Database connection timeout errors appear.
- Connection pool utilization reaches 100 percent.

Investigation:
1. Check database CPU, connections, and active sessions.
2. Check application connection pool usage.
3. Review recent deployments.
4. Check for long-running queries.

Approved remediation:
1. Scale application instances if database capacity permits.
2. Restart unhealthy application instances after approval.
3. Roll back a recent deployment after approval.
4. Change connection pool settings through change management.

Never restart database servers automatically.
Human approval is required before remediation.
                """,
            },
            {
                "id": "historical-payment-incident",
                "title": "Historical Payment API Incident",
                "type": "historical_incident",
                "content": """
The Payment API returned HTTP 500 errors after a deployment.

Root cause:
A retry feature created too many concurrent database connections.
The application connection pool became exhausted.

Evidence:
- Database timeout errors.
- Connection pool utilization was 100 percent.
- The incident started shortly after deployment.

Resolution:
The deployment was rolled back after on-call approval.
                """,
            },
            {
                "id": "rollback-runbook",
                "title": "Application Deployment Rollback Runbook",
                "type": "runbook",
                "content": """
Use this runbook when service degradation begins after a deployment.

Steps:
1. Compare deployment time with incident start time.
2. Review deployment version and configuration changes.
3. Request human approval.
4. Roll back to the previous stable version.
5. Monitor error rates after rollback.
                """,
            },
        ]

        self.add_documents(documents)

    def add_documents(self, documents: list[dict[str, str]]) -> None:
        self.collection.add(
            ids=[item["id"] for item in documents],
            documents=[item["content"] for item in documents],
            metadatas=[
                {
                    "title": item["title"],
                    "document_type": item["type"],
                }
                for item in documents
            ],
        )

    def add_document(
        self,
        title: str,
        content: str,
        document_type: str,
    ) -> str:
        import uuid

        document_id = str(uuid.uuid4())

        self.collection.add(
            ids=[document_id],
            documents=[content],
            metadatas=[
                {
                    "title": title,
                    "document_type": document_type,
                }
            ],
        )

        return document_id

    def search(
        self,
        query: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        if self.collection.count() == 0:
            return []

        result = self.collection.query(
            query_texts=[query],
            n_results=min(limit, self.collection.count()),
        )

        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        document_ids = result["ids"][0]

        matches = []

        for document, metadata, distance, document_id in zip(
            documents,
            metadatas,
            distances,
            document_ids,
        ):
            matches.append(
                {
                    "id": document_id,
                    "title": metadata.get("title"),
                    "document_type": metadata.get("document_type"),
                    "content": document,
                    "distance": round(float(distance), 4),
                }
            )

        return matches