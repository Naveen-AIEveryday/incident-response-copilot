import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


class Database:
    def __init__(self, path: str):
        self.path = path
        self.create_tables()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_tables(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    logs TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result TEXT
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

    def create_incident(
        self,
        incident_id: str,
        incident: dict[str, str],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO incidents (
                    incident_id,
                    title,
                    description,
                    logs,
                    status,
                    created_at,
                    result
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    incident["title"],
                    incident["description"],
                    incident["logs"],
                    "investigating",
                    self.now(),
                    None,
                ),
            )

    def update_incident(
        self,
        incident_id: str,
        status: str,
        result: dict[str, Any],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE incidents
                SET status = ?, result = ?
                WHERE incident_id = ?
                """,
                (
                    status,
                    json.dumps(result),
                    incident_id,
                ),
            )

    def get_incident(
        self,
        incident_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
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

        if incident["result"]:
            incident["result"] = json.loads(
                incident["result"]
            )
        else:
            incident["result"] = None

        return incident

    def list_incidents(
        self,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM incidents
                ORDER BY created_at DESC
                """
            ).fetchall()

        incidents = []

        for row in rows:
            incident = dict(row)

            if incident["result"]:
                incident["result"] = json.loads(
                    incident["result"]
                )
            else:
                incident["result"] = None

            incidents.append(incident)

        return incidents

    def add_event(
        self,
        incident_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        with self.connect() as connection:
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

    def get_events(
        self,
        incident_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM audit_events
                WHERE incident_id = ?
                ORDER BY created_at
                """,
                (incident_id,),
            ).fetchall()

        events = []

        for row in rows:
            event = dict(row)
            event["details"] = json.loads(
                event["details"]
            )
            events.append(event)

        return events