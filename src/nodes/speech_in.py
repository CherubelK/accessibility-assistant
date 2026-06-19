import tempfile

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import write as write_wav

from src.config import GENERIC_ERROR_MESSAGES, LANGUAGES, WHISPER_MODEL_SIZE
from src.state import AssistantState

SAMPLE_RATE = 16000
_whisper_model = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def record_audio(seconds: float = 6.0) -> str:
    """Records `seconds` of mic audio and returns a temp WAV file path."""
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    path = f"{tempfile.gettempdir()}/mic_input.wav"
    write_wav(path, SAMPLE_RATE, audio)
    return path


def speech_in_node(state: AssistantState) -> dict:
    print(f"[speech_in] state in: {state}")

    language = state.get("target_language", "Spanish")

    try:
        wav_path = record_audio()
        language_code = LANGUAGES.get(language, (None,))[0]

        model = _get_whisper_model()
        segments, _ = model.transcribe(wav_path, language=language_code)
        transcript = " ".join(segment.text.strip() for segment in segments)
    except Exception as exc:
        print(f"[speech_in] failed: {exc}")
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    if not transcript:
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    result = {"user_request": transcript}
    print(f"[speech_in] state out: {result}")
    return result


def transcribe_file(wav_path: str, language_code: str | None = None) -> str:
    """Helper for testing: transcribes an existing WAV file instead of the mic."""
    model = _get_whisper_model()
    segments, _ = model.transcribe(wav_path, language=language_code)
    return " ".join(segment.text.strip() for segment in segments)
