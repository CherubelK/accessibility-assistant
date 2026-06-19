import tempfile
import wave

import sounddevice as sd
from piper import PiperVoice

from src.config import piper_model_path
from src.state import AssistantState

_voice_cache: dict[str, PiperVoice] = {}


def _get_voice(language: str) -> PiperVoice:
    if language not in _voice_cache:
        _voice_cache[language] = PiperVoice.load(piper_model_path(language))
    return _voice_cache[language]


def synthesize_to_wav(text: str, language: str, output_path: str | None = None) -> str:
    voice = _get_voice(language)
    output_path = output_path or f"{tempfile.gettempdir()}/tts_output.wav"

    with wave.open(output_path, "wb") as wav_file:
        chunks = list(voice.synthesize(text))
        wav_file.setnchannels(chunks[0].sample_channels)
        wav_file.setsampwidth(chunks[0].sample_width)
        wav_file.setframerate(chunks[0].sample_rate)
        for chunk in chunks:
            wav_file.writeframes(chunk.audio_int16_bytes)

    return output_path


def play_wav(path: str) -> None:
    with wave.open(path, "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()

    import numpy as np
    audio = np.frombuffer(frames, dtype="int16").reshape(-1, channels)
    sd.play(audio, samplerate=sample_rate)
    sd.wait()


def speech_out_node(state: AssistantState) -> dict:
    print(f"[speech_out] state in: { {k: v for k, v in state.items() if k != 'raw_screen_text'} }")

    text = state["simplified_text"]
    language = state.get("target_language", "Spanish")

    audio_path = synthesize_to_wav(text, language)
    play_wav(audio_path)

    result = {"audio_path": audio_path}
    print(f"[speech_out] state out: {result}")
    return result
