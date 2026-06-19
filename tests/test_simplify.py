"""Tests for the simplify/translate chain and related config helpers.

The model tests call the real local phi4-mini via Ollama (no mocking --
this project's whole point is "everything runs locally", so a fake LLM
response wouldn't tell us anything useful). They require `ollama serve`
running with phi4-mini pulled, and are slower than a typical unit test.
"""

import pytest

from src.config import has_voice, piper_model_path
from src.nodes.simplify import simplify_node

SAMPLE_TEXT = (
    "Your application for benefits has been received. To avoid a lapse in "
    "coverage, you must submit Form RRB-1099 and proof of income within 30 "
    "days of the date on this notice. Failure to respond may result in "
    "termination of benefits."
)


@pytest.mark.requires_ollama
def test_simplify_preserves_key_facts():
    result = simplify_node({"user_request": SAMPLE_TEXT, "target_language": "Spanish"})

    assert "error" not in result
    text = result["simplified_text"]
    assert "RRB-1099" in text
    assert "30" in text


def test_simplify_node_missing_text_returns_graceful_error():
    result = simplify_node({"target_language": "Spanish"})

    assert "simplified_text" not in result
    assert result["error"]


def test_has_voice():
    assert has_voice("Spanish") is True
    assert has_voice("English") is False


def test_piper_model_path_raises_for_voiceless_language():
    with pytest.raises(ValueError):
        piper_model_path("English")
