"""Desktop entry point: runs the Streamlit homepage in a native window
instead of a browser tab. First step toward a downloadable desktop app --
launch this instead of `streamlit run` to get an app-like window.

Usage: python -m src.desktop
"""

import socket
import subprocess
import sys
import time

import webview

PORT = 8501


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


def _wait_for_server(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_is_open(port):
            return
        time.sleep(0.3)
    raise RuntimeError(f"Streamlit server did not start on port {port} within {timeout}s")


def main() -> None:
    server = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "src/app.py",
        "--server.port", str(PORT),
    ])

    try:
        _wait_for_server(PORT)
        webview.create_window("Accessibility Assistant", f"http://localhost:{PORT}", width=900, height=750)
        webview.start()
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    main()
