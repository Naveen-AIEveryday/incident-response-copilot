from fastapi import FastAPI

from app.agents import IncidentAgents
from app.config import API_HOST, API_PORT, SQLITE_PATH
from app.database import Database
from app.knowledge_base import KnowledgeBase
from app.orchestrator import Orchestrator
from app.routes import create_routes


database = Database(SQLITE_PATH)
knowledge_base = KnowledgeBase()
agents = IncidentAgents()

orchestrator = Orchestrator(
    database=database,
    knowledge_base=knowledge_base,
    agents=agents,
)

app = FastAPI(
    title="Incident Response Copilot",
)

app.include_router(
    create_routes(orchestrator)
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
    )