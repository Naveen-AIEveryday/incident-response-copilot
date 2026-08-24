import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.knowledge_base import KnowledgeBase
from app.models import IncidentRequest
from app.orchestrator import Orchestrator
from app.routes import create_routes
from fastapi import FastAPI


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = Database(db_path)
    yield db
    try:
        os.remove(db_path)
    except Exception:
        pass


@pytest.fixture
def temp_kb():
    tmpdir = tempfile.mkdtemp()
    kb = KnowledgeBase(chroma_path=tmpdir)
    yield kb
    try:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass



def test_database_crud_and_search(temp_db):
    temp_db.create_incident(
        incident_id="test-123",
        incident={
            "title": "Payment gateway timeout",
            "description": "500 errors on checkout",
            "logs": "TimeoutException at payment.db",
        },
    )

    inc = temp_db.get_incident("test-123")
    assert inc is not None
    assert inc["title"] == "Payment gateway timeout"
    assert inc["status"] == "investigating"

    temp_db.update_incident_status("test-123", "remediation_approved")
    inc_updated = temp_db.get_incident("test-123")
    assert inc_updated["status"] == "remediation_approved"

    # Search filter
    filtered = temp_db.list_incidents(status="remediation_approved", search_query="Payment")
    assert len(filtered) == 1
    assert filtered[0]["incident_id"] == "test-123"

    # Audit events
    temp_db.add_event("test-123", "test_event", {"info": "all good"})
    events = temp_db.get_events("test-123")
    assert len(events) == 1
    assert events[0]["event_type"] == "test_event"

    # Delete
    deleted = temp_db.delete_incident("test-123")
    assert deleted is True
    assert temp_db.get_incident("test-123") is None


def test_knowledge_base_hybrid_search(temp_kb):
    # Search for database connection issues
    results = temp_kb.search("Database connection pool exhausted timeout HTTP 500", limit=2)
    assert len(results) >= 1
    assert "Database Connection Pool" in results[0]["title"]
    assert results[0]["score"] > 0

    # Add new runbook dynamically
    new_doc = temp_kb.add_document(
        title="Redis Eviction Runbook",
        content="Symptoms: High memory on Redis. Resolution: Increase maxmemory or restart Redis.",
        document_type="runbook",
        tags=["redis", "cache", "memory"],
    )
    assert new_doc["id"].startswith("doc-")

    # Search for the newly added runbook
    redis_results = temp_kb.search("Redis cache memory eviction", limit=1)
    assert len(redis_results) >= 1
    assert "Redis" in redis_results[0]["title"]

    # Delete runbook
    deleted = temp_kb.delete_document(new_doc["id"])
    assert deleted is True


def test_api_routes_with_testclient(temp_db, temp_kb):
    class MockAgents:
        pass

    orchestrator = Orchestrator(
        database=temp_db,
        knowledge_base=temp_kb,
        agents=MockAgents(),
    )

    app = FastAPI()
    app.include_router(create_routes(orchestrator))
    client = TestClient(app)

    # Health check
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["version"] == "2.0"

    # Knowledge list
    res_kb = client.get("/knowledge/runbooks")
    assert res_kb.status_code == 200
    assert len(res_kb.json()) >= 5

    # Create runbook via API
    res_add = client.post(
        "/knowledge/runbooks",
        json={
            "title": "Kafka Broker Down Runbook",
            "content": "Check zookeeper and broker partition lags.",
            "document_type": "runbook",
            "tags": ["kafka", "queue"],
        },
    )
    assert res_add.status_code == 200
    created_id = res_add.json()["id"]

    # Search runbooks via API
    res_search = client.get("/knowledge/search", params={"q": "Kafka partition lag"})
    assert res_search.status_code == 200
    assert any("Kafka" in item["title"] for item in res_search.json())

    # Delete runbook via API
    res_del = client.delete(f"/knowledge/runbooks/{created_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True
