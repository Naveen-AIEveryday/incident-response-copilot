import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent


def wait_for_http(url: str, timeout_seconds: int = 40) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env["API_HOST"] = "127.0.0.1"
    env["API_PORT"] = "9002"
    env["API_URL"] = "http://127.0.0.1:9002"
    env["STREAMLIT_HOST"] = "127.0.0.1"
    env["STREAMLIT_PORT"] = "8502"
    env["STREAMLIT_URL"] = "http://127.0.0.1:8502"
    return env


def main() -> None:
    env = build_env()
    backend_url = env["API_URL"]
    streamlit_url = env["STREAMLIT_URL"]

    backend = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=str(ROOT),
        env=env,
    )

    try:
        if not wait_for_http(f"{backend_url}/", timeout_seconds=30):
            raise RuntimeError(f"Backend did not start on {backend_url}")

        streamlit = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "ui/streamlit_app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                env["STREAMLIT_PORT"],
                "--server.headless",
                "true",
            ],
            cwd=str(ROOT),
            env=env,
        )

        try:
            if not wait_for_http(streamlit_url, timeout_seconds=30):
                raise RuntimeError(f"Streamlit did not start on {streamlit_url}")

            print(f"Backend running: {backend_url}")
            print(f"Streamlit running: {streamlit_url}")
            print("Press Ctrl+C to stop both services.")

            while True:
                time.sleep(1)
        finally:
            streamlit.terminate()
            streamlit.wait(timeout=20)
    except KeyboardInterrupt:
        pass
    finally:
        backend.terminate()
        backend.wait(timeout=20)


if __name__ == "__main__":
    main()
