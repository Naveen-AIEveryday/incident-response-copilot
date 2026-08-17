from fastapi import FastAPI

from app.agents import IncidentAgents
from app.config import API_HOST, API_PORT, SQLITE_PATH
from app.database import AuditDatabase
from app.knowledge_base import KnowledgeBase
from app.orchestrator import IncidentOrchestrator
from app.routes import create_router


database = AuditDatabase(SQLITE_PATH)
knowledge_base = KnowledgeBase()
agents = IncidentAgents()

orchestrator = IncidentOrchestrator(
    database=database,
    knowledge_base=knowledge_base,
    agents=agents,
)

app = FastAPI(
    title="Agentic IT Incident Response Copilot",
    version="1.0.0",
)

app.include_router(create_router(orchestrator))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )