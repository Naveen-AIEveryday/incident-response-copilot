import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


class AuditDatabase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    logs TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result_json TEXT
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_incident(
        self,
        incident_id: str,
        title: str,
        description: str,
        logs: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO incidents (
                    incident_id,
                    title,
                    description,
                    logs,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    title,
                    description,
                    logs,
                    "investigating",
                    self.now(),
                ),
            )

    def update_incident(
        self,
        incident_id: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        result_json = json.dumps(result) if result else None

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE incidents
                SET status = ?, result_json = ?
                WHERE incident_id = ?
                """,
                (status, result_json, incident_id),
            )

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM incidents
                WHERE incident_id = ?
                """,
                (incident_id,),
            ).fetchone()

        if row is None:
            return None

        incident = dict(row)

        if incident["result_json"]:
            incident["result"] = json.loads(incident["result_json"])
        else:
            incident["result"] = None

        incident.pop("result_json", None)
        return incident

    def add_event(
        self,
        incident_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    event_id,
                    incident_id,
                    event_type,
                    details,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    incident_id,
                    event_type,
                    json.dumps(details),
                    self.now(),
                ),
            )

    def get_events(self, incident_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, event_type, details, created_at
                FROM audit_events
                WHERE incident_id = ?
                ORDER BY created_at
                """,
                (incident_id,),
            ).fetchall()

        events = []

        for row in rows:
            event = dict(row)
            event["details"] = json.loads(event["details"])
            events.append(event)

        return events