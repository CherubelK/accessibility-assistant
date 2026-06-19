from typing import TypedDict, Optional


class AssistantState(TypedDict, total=False):
    # input
    user_request: str          # what the person asked (typed or transcribed)
    target_language: str       # e.g. "Spanish"
    screenshot_path: Optional[str]
    text_model: str             # which Ollama model simplify.py should use (fast vs. quality)

    # routing flags (set by the caller, consumed by graph.route_start / route_after_simplify)
    capture_screen: bool        # True -> grab a live screenshot before reading it
    record_voice: bool          # True -> record from the mic instead of using user_request
    speak_output: bool          # True -> synthesize + play simplified_text after simplify

    # intermediate
    raw_screen_text: str       # vision + OCR output
    ocr_text: Optional[str]    # exact text from Tesseract, if used

    # output
    simplified_text: str       # plain-language translation
    audio_path: Optional[str]  # path to spoken-version audio file

    # control / safety
    needs_confirmation: bool   # gate before any consequential action
    error: Optional[str]
