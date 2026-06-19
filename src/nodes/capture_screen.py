import tempfile
import time

import mss
from langgraph.types import interrupt

from src.config import CAPTURE_CANCELLED_MESSAGES, GENERIC_ERROR_MESSAGES, SCREEN_CAPTURE_CONFIRM_MESSAGES
from src.nodes._timing import timed_node
from src.state import AssistantState


def confirm_screen_capture_node(state: AssistantState) -> dict:
    """Human-in-the-loop gate: a screenshot reads everything currently
    visible, not just the document the user means to share, so this pauses
    the graph and waits for explicit approval before capture_screen_node
    runs. Nothing else happens in this node (no side effects) so re-running
    it on resume is harmless."""
    language = state.get("target_language", "Spanish")
    message = SCREEN_CAPTURE_CONFIRM_MESSAGES.get(language, SCREEN_CAPTURE_CONFIRM_MESSAGES["English"])
    confirmed = bool(interrupt({"message": message}))
    if not confirmed:
        return {
            "capture_confirmed": False,
            "info": CAPTURE_CANCELLED_MESSAGES.get(language, CAPTURE_CANCELLED_MESSAGES["English"]),
        }
    return {"capture_confirmed": True}


@timed_node("capture_screen")
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
