import os

from dotenv import load_dotenv


load_dotenv()

# Ollama configuration
OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2",
)

# Local application storage
CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    "./data/chroma",
)

SQLITE_PATH = os.getenv(
    "SQLITE_PATH",
    "./data/incidents.db",
)

# FastAPI backend configuration
API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1",
)

API_PORT = int(
    os.getenv(
        "API_PORT",
        "8000",
    )
)

# URL used by the Streamlit UI to call FastAPI
API_URL = os.getenv(
    "API_URL",
    f"http://{API_HOST}:{API_PORT}"
)

# Create required local folders automatically
os.makedirs(CHROMA_PATH, exist_ok=True)
os.makedirs(
    os.path.dirname(SQLITE_PATH) or ".",
    exist_ok=True,
)