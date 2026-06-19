import tempfile
import time

import mss

from src.state import AssistantState


def capture_screen_node(state: AssistantState) -> dict:
    print(f"[capture_screen] state in: {state}")

    path = f"{tempfile.gettempdir()}/screenshot_{int(time.time())}.png"
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        shot = sct.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=path)

    result = {"screenshot_path": path}
    print(f"[capture_screen] state out: {result}")
    return result
