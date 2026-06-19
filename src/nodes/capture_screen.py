import tempfile
import time

import mss

from src.config import GENERIC_ERROR_MESSAGES
from src.state import AssistantState


def capture_screen_node(state: AssistantState) -> dict:
    print(f"[capture_screen] state in: {state}")

    language = state.get("target_language", "Spanish")
    path = f"{tempfile.gettempdir()}/screenshot_{int(time.time())}.png"

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            shot = sct.grab(monitor)
            mss.tools.to_png(shot.rgb, shot.size, output=path)
    except Exception as exc:
        print(f"[capture_screen] failed: {exc}")
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    result = {"screenshot_path": path}
    print(f"[capture_screen] state out: {result}")
    return result
