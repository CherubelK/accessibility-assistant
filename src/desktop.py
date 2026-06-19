"""Desktop entry point: runs the Streamlit homepage in a native window
instead of a browser tab. First step toward a downloadable desktop app --
launch this instead of `streamlit run` to get an app-like window.

Runs the Streamlit server in-process via streamlit.web.bootstrap (rather
than spawning `python -m streamlit` as a subprocess) so this also works
once frozen into a standalone .exe, where there's no separate `python`
executable to spawn.

Usage: python -m src.desktop
"""

import os
import socket
import threading
import time

import webview
from streamlit.web import bootstrap

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


def _run_streamlit() -> None:
    # bootstrap.run installs a SIGTERM handler, which only works on the main
    # thread -- but pywebview needs the main thread for its own GUI loop, so
    # Streamlit runs here on a background thread instead. We don't need
    # graceful SIGTERM handling for this embedded use case (the whole
    # process exits when the window closes), so no-op it out.
    bootstrap._set_up_signal_handler = lambda *args, **kwargs: None

    # NOTE: keys are config option names with "." replaced by "_" -- this
    # matches the click-option dest names `streamlit run` itself passes
    # to bootstrap.run (see _convert_config_option_to_click_option in
    # streamlit/web/cli.py: `param = config_option.key.replace(".", "_")`).
    # Dotted keys like "server.port" are silently ignored.
    flag_options = {
        "server_port": PORT,
        "server_address": "localhost",
        "server_headless": True,
        "browser_gatherUsageStats": False,
        # Streamlit's "are we installed normally" heuristic checks for
        # "site-packages" in its own __file__ path. PyInstaller relocates
        # everything into _internal/, so that check always misfires once
        # frozen, silently disabling static asset serving (404 on "/").
        # Force it off explicitly.
        "global_developmentMode": False,
    }

    # bootstrap.run()'s internal _install_config_watchers() only sets up
    # *future* config-file-change watchers -- it does NOT apply flag_options
    # immediately. The actual `streamlit run` CLI applies them by calling
    # load_config_options() itself before calling run() (see web/cli.py);
    # we have to do the same here or every flag above is silently ignored.
    bootstrap.load_config_options(flag_options=flag_options)

    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    bootstrap.run(app_path, is_hello=False, args=[], flag_options=flag_options)


def main() -> None:
    threading.Thread(target=_run_streamlit, daemon=True).start()
    _wait_for_server(PORT)
    webview.create_window("Accessibility Assistant", f"http://localhost:{PORT}", width=900, height=750)
    webview.start()


if __name__ == "__main__":
    main()
