import base64
import shutil
import time

import pytesseract
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from PIL import Image

from src.config import GENERIC_ERROR_MESSAGES, VISION_MODEL
from src.nodes._timing import timed_node
from src.state import AssistantState

# num_predict caps the response length -- vision models on CPU can otherwise
# fall into a repetition loop and generate thousands of tokens without
# stopping (observed: 6500+ tokens at ~3 tok/s on this hardware).
vision = ChatOllama(model=VISION_MODEL, temperature=0.1, num_predict=400)

# On Windows, Tesseract isn't always on PATH after install; fall back to the
# default UB-Mannheim install location if `tesseract` isn't found.
if shutil.which("tesseract") is None:
    default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = default_win_path


# Below this many OCR characters, assume the screen is mostly non-text
# (e.g. a photo, icon-heavy UI) and it's worth the slow vision call. Above
# it, OCR alone is enough -- and it's near-instant vs. ~1-2 minutes for the
# vision model on CPU, which matters a lot for a "read my screen" feature
# that's supposed to feel responsive.
MIN_OCR_CHARS_TO_SKIP_VISION = 40


def _read_with_vision(screenshot_path: str) -> str | None:
    try:
        with open(screenshot_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        message = HumanMessage(content=[
            {
                "type": "text",
                "text": (
                    "Read this screen and describe what it says and what the user "
                    "is being asked to do. Be literal -- do not infer or invent "
                    "details that are not visible."
                ),
            },
            {"type": "image", "base64": image_b64, "mime_type": "image/png"},
        ])
        return vision.invoke([message]).content
    except Exception as exc:
        print(f"[read_screen] vision failed: {exc}")
        return None


@timed_node("read_screen")
def read_screen_node(state: AssistantState) -> dict:
    print(f"[read_screen] state in: {state}")

    screenshot_path = state["screenshot_path"]
    language = state.get("target_language", "Spanish")

    ocr_start = time.time()
    try:
        ocr_text = pytesseract.image_to_string(Image.open(screenshot_path)).strip()
    except Exception as exc:
        ocr_text = None
        print(f"[read_screen] OCR failed: {exc}")
    print(f"[read_screen] OCR took {time.time() - ocr_start:.1f}s")

    vision_text = None
    if not ocr_text or len(ocr_text) < MIN_OCR_CHARS_TO_SKIP_VISION:
        print("[read_screen] OCR text too short/empty, falling back to vision (slow)")
        vision_start = time.time()
        vision_text = _read_with_vision(screenshot_path)
        print(f"[read_screen] vision call took {time.time() - vision_start:.1f}s")
    else:
        print(f"[read_screen] OCR got {len(ocr_text)} chars, skipping vision call for speed")

    if not vision_text and not ocr_text:
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    raw_screen_text = vision_text or ""
    if ocr_text:
        raw_screen_text += f"\n\n--- Exact OCR text ---\n{ocr_text}"

    result = {"raw_screen_text": raw_screen_text.strip(), "ocr_text": ocr_text}
    print(f"[read_screen] state out: { {k: v for k, v in result.items()} }")
    return result
