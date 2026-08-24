import os
import socket
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def find_free_port(
    start_port: int,
    host: str = "127.0.0.1",
    max_tries: int = 20,
) -> int:
    """Return the first free localhost port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue

    raise RuntimeError(
        f"Could not find a free port starting at {start_port}."
    )


def resolve_port(
    configured_value: str | None,
    fallback_port: int,
    host: str = "127.0.0.1",
) -> int:
    """Use the configured port when present, otherwise fall back to a stable default."""
    if configured_value is None:
        return fallback_port

    try:
        port = int(configured_value)
    except ValueError:
        return fallback_port

    return port


def get_backend_candidates() -> list[str]:
    """Return the configured API URL first and then common local fallbacks."""
    host = os.getenv("API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    configured_port = os.getenv("API_PORT", "9002").strip() or "9002"

    try:
        configured_port_int = int(configured_port)
    except ValueError:
        configured_port_int = 9002

    candidates: list[str] = []
    configured_url = os.getenv("API_URL", "").strip()
    if configured_url:
        candidates.append(configured_url.rstrip("/"))

    for port in [configured_port_int, 8000, 9001, 9002, 8501, 8080, 5000]:
        candidate = f"http://{host}:{port}"
        if candidate not in candidates:
            candidates.append(candidate)

    localhost_candidate = f"http://localhost:{configured_port_int}"
    if localhost_candidate not in candidates:
        candidates.append(localhost_candidate)

    return candidates


STREAMLIT_HOST = os.getenv(
    "STREAMLIT_HOST",
    "127.0.0.1",
)

STREAMLIT_PORT = int(
    os.getenv(
        "STREAMLIT_PORT",
        "8502",
    )
)

STREAMLIT_URL = os.getenv(
    "STREAMLIT_URL",
    f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}",
)


OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434/v1",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2",
)

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "local",
).strip().lower()

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY",
    "",
)

OLLAMA_CLOUD_BASE_URL = os.getenv(
    "OLLAMA_CLOUD_BASE_URL",
    "https://ollama.com/v1",
)

OLLAMA_CLOUD_MODEL = os.getenv(
    "OLLAMA_CLOUD_MODEL",
    OLLAMA_MODEL,
)

ACTIVE_LLM_PROVIDER = (
    "local" if LLM_PROVIDER not in {"local", "cloud"} else LLM_PROVIDER
)

ACTIVE_OLLAMA_API_KEY = (
    "ollama"
    if ACTIVE_LLM_PROVIDER == "local"
    else OLLAMA_API_KEY
)

ACTIVE_OLLAMA_BASE_URL = (
    OLLAMA_HOST
    if ACTIVE_LLM_PROVIDER == "local"
    else OLLAMA_CLOUD_BASE_URL
)

ACTIVE_OLLAMA_MODEL = (
    OLLAMA_MODEL
    if ACTIVE_LLM_PROVIDER == "local"
    else OLLAMA_CLOUD_MODEL
)

API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1",
)

default_api_port = int(
    os.getenv(
        "API_PORT",
        "9002",
    )
)
API_PORT = resolve_port(
    os.getenv("API_PORT"),
    default_api_port,
    host=API_HOST,
)

API_URL = (
    os.getenv("API_URL", f"http://{API_HOST}:{API_PORT}")
    .rstrip("/")
)

GRADIO_HOST = os.getenv(
    "GRADIO_HOST",
    "127.0.0.1",
)

default_gradio_port = int(
    os.getenv(
        "GRADIO_PORT",
        "7860",
    )
)
GRADIO_PORT = resolve_port(
    os.getenv("GRADIO_PORT"),
    default_gradio_port,
    host=GRADIO_HOST,
)

SQLITE_PATH = os.getenv(
    "SQLITE_PATH",
    "./data/incidents.db",
)

Path(SQLITE_PATH).parent.mkdir(
    parents=True,
    exist_ok=True,
)

CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    "./data/chroma",
)

Path(CHROMA_PATH).mkdir(
    parents=True,
    exist_ok=True,
)