import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_TEXT_MODEL = os.getenv("DEFAULT_TEXT_MODEL", "phi4-mini")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "Spanish")

VISION_MODEL = os.getenv("VISION_MODEL", "gemma3:12b")
QUALITY_TEXT_MODEL = os.getenv("QUALITY_TEXT_MODEL", "qwen3:8b")

# faster-whisper STT model size. "small" is a good CPU speed/accuracy
# tradeoff on the target hardware (16GB RAM, no GPU).
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")

PIPER_VOICES_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "piper")

# Supported languages: display name -> (Whisper language code, Piper voice file stem).
# All voices are open-weight, downloaded once into models/piper/.
LANGUAGES = {
    "Spanish": ("es", "es_ES-davefx-medium"),
    "Chinese": ("zh", "zh_CN-huayan-medium"),
    "Vietnamese": ("vi", "vi_VN-vais1000-medium"),
    "Arabic": ("ar", "ar_JO-kareem-medium"),
    "Russian": ("ru", "ru_RU-denis-medium"),
    "French": ("fr", "fr_FR-siwis-medium"),
    "Portuguese": ("pt", "pt_BR-faber-medium"),
    "Hindi": ("hi", "hi_IN-pratham-medium"),
    "Urdu": ("ur", "ur_PK-fasih-medium"),
    "Persian": ("fa", "fa_IR-amir-medium"),
    "English": ("en", None),  # pass-through, no translation/TTS voice needed
}


def piper_model_path(language: str) -> str:
    _, voice_stem = LANGUAGES[language]
    if voice_stem is None:
        raise ValueError(f"No Piper voice configured for {language}")
    return os.path.join(PIPER_VOICES_DIR, f"{voice_stem}.onnx")
