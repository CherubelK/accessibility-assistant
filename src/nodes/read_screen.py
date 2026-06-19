import base64
import shutil

import pytesseract
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from PIL import Image

from src.config import VISION_MODEL
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


def read_screen_node(state: AssistantState) -> dict:
    print(f"[read_screen] state in: {state}")

    screenshot_path = state["screenshot_path"]

    try:
        ocr_text = pytesseract.image_to_string(Image.open(screenshot_path)).strip()
    except Exception as exc:
        ocr_text = None
        print(f"[read_screen] OCR failed, continuing with vision only: {exc}")

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
    vision_result = vision.invoke([message])

    raw_screen_text = vision_result.content
    if ocr_text:
        raw_screen_text += f"\n\n--- Exact OCR text ---\n{ocr_text}"

    result = {"raw_screen_text": raw_screen_text, "ocr_text": ocr_text}
    print(f"[read_screen] state out: { {k: v for k, v in result.items()} }")
    return result
