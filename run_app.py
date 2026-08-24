import argparse
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
    env["GRADIO_HOST"] = "127.0.0.1"
    env["GRADIO_PORT"] = "7860"
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Incident Response Copilot")
    parser.add_argument(
        "--ui",
        choices=["streamlit", "gradio"],
        default="streamlit",
        help="UI framework to launch: 'streamlit' (default) or 'gradio'",
    )
    args = parser.parse_args()

    env = build_env()
    backend_url = env["API_URL"]

    backend = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=str(ROOT),
        env=env,
    )

    try:
        if not wait_for_http(f"{backend_url}/", timeout_seconds=30):
            raise RuntimeError(f"Backend did not start on {backend_url}")

        if args.ui == "gradio":
            gradio_url = f"http://127.0.0.1:{env['GRADIO_PORT']}"
            ui_proc = subprocess.Popen(
                [sys.executable, "ui/gradio_app.py"],
                cwd=str(ROOT),
                env=env,
            )
            ui_url = gradio_url
            ui_name = "Gradio"
        else:
            streamlit_url = env["STREAMLIT_URL"]
            ui_proc = subprocess.Popen(
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
            ui_url = streamlit_url
            ui_name = "Streamlit"

        try:
            if not wait_for_http(ui_url, timeout_seconds=30):
                raise RuntimeError(f"{ui_name} did not start on {ui_url}")

            print(f"Backend running: {backend_url}")
            print(f"{ui_name} UI running: {ui_url}")
            print("Press Ctrl+C to stop both services.")

            while True:
                time.sleep(1)
        finally:
            ui_proc.terminate()
            ui_proc.wait(timeout=20)
    except KeyboardInterrupt:
        pass
    finally:
        backend.terminate()
        backend.wait(timeout=20)


if __name__ == "__main__":
    main()

