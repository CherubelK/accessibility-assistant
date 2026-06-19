"""Pre-flight checks so a non-technical user sees a clear instruction
("Ollama isn't running -- start it and try again") instead of a Python
traceback the first time something in the chain isn't set up yet.
"""

import requests

from src.config import LANGUAGES, OLLAMA_BASE_URL, PIPER_VOICES_DIR, VISION_MODEL, has_voice, piper_model_path

REQUIRED_OLLAMA_MODELS = ["phi4-mini", "qwen3:8b", VISION_MODEL]


def check_ollama_models() -> list[str]:
    """Returns a list of human-readable problems. Empty list means all good."""
    problems = []

    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        response.raise_for_status()
    except requests.RequestException:
        problems.append(
            f"Can't reach Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is installed "
            "and running, then reload this page."
        )
        return problems

    # Ollama appends ":latest" to tags that don't specify one (e.g. "phi4-mini"
    # is reported back as "phi4-mini:latest"), so compare with that stripped.
    installed = {m["name"].removesuffix(":latest") for m in response.json().get("models", [])}
    for model in REQUIRED_OLLAMA_MODELS:
        if model.removesuffix(":latest") not in installed:
            problems.append(f"Model \"{model}\" isn't pulled yet. Run: ollama pull {model}")

    return problems


def check_piper_voices() -> list[str]:
    import os

    problems = []
    missing = [lang for lang in LANGUAGES if has_voice(lang) and not os.path.exists(piper_model_path(lang))]
    if missing:
        problems.append(
            f"Voice models missing for: {', '.join(missing)}. "
            f"Run: bash models/download_voices.sh (expects to write into {PIPER_VOICES_DIR})"
        )
    return problems


def run_all_checks() -> list[str]:
    return check_ollama_models() + check_piper_voices()
