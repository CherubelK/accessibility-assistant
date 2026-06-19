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


def has_voice(language: str) -> bool:
    return LANGUAGES[language][1] is not None


def piper_model_path(language: str) -> str:
    _, voice_stem = LANGUAGES[language]
    if voice_stem is None:
        raise ValueError(f"No Piper voice configured for {language}")
    return os.path.join(PIPER_VOICES_DIR, f"{voice_stem}.onnx")


# Generic "something went wrong" messages shown when a node fails, in each
# supported language, so an error is never shown only in English to someone
# who doesn't read it.
GENERIC_ERROR_MESSAGES = {
    "Spanish": "Algo salió mal. Por favor, inténtalo de nuevo.",
    "Chinese": "出了点问题。请再试一次。",
    "Vietnamese": "Đã xảy ra lỗi. Vui lòng thử lại.",
    "Arabic": "حدث خطأ ما. يرجى المحاولة مرة أخرى.",
    "Russian": "Что-то пошло не так. Пожалуйста, попробуйте снова.",
    "French": "Quelque chose s'est mal passé. Veuillez réessayer.",
    "Portuguese": "Algo deu errado. Por favor, tente novamente.",
    "Hindi": "कुछ गलत हो गया। कृपया फिर से प्रयास करें।",
    "Urdu": "کچھ غلط ہو گیا۔ براہ کرم دوبارہ کوشش کریں۔",
    "Persian": "مشکلی پیش آمد. لطفاً دوباره تلاش کنید.",
    "English": "Something went wrong. Please try again.",
}

# Shown specifically when the mic recorded nothing recognizable as speech --
# distinct from GENERIC_ERROR_MESSAGES because this isn't a technical
# failure, just "I didn't catch that."
NO_SPEECH_DETECTED_MESSAGES = {
    "Spanish": "No escuché nada. Inténtalo de nuevo y habla con claridad.",
    "Chinese": "我没有听到任何内容。请再试一次,清楚地说话。",
    "Vietnamese": "Tôi không nghe thấy gì. Vui lòng thử lại và nói rõ.",
    "Arabic": "لم أسمع أي شيء. حاول مرة أخرى وتحدث بوضوح.",
    "Russian": "Я ничего не услышал. Попробуйте снова и говорите чётко.",
    "French": "Je n'ai rien entendu. Réessayez en parlant clairement.",
    "Portuguese": "Não ouvi nada. Tente novamente e fale claramente.",
    "Hindi": "मुझे कुछ सुनाई नहीं दिया। कृपया फिर से कोशिश करें और स्पष्ट रूप से बोलें।",
    "Urdu": "مجھے کچھ سنائی نہیں دیا۔ دوبارہ کوشش کریں اور واضح طور پر بولیں۔",
    "Persian": "چیزی نشنیدم. دوباره تلاش کنید و واضح صحبت کنید.",
    "English": "I didn't hear anything. Please try again and speak clearly.",
}
