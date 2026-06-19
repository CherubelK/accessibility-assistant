"""Tests for src/setup_check.py. Mocks the Ollama HTTP API so these run
without a live Ollama server -- unlike tests/test_simplify.py, which
deliberately calls the real local model.
"""

from unittest.mock import MagicMock, patch

from src.setup_check import check_ollama_models


def _mock_tags_response(model_names):
    response = MagicMock()
    response.json.return_value = {"models": [{"name": name} for name in model_names]}
    return response


def test_check_ollama_models_handles_implicit_latest_tag():
    # Ollama reports back "phi4-mini" (no explicit tag) as "phi4-mini:latest".
    # A previous version of this check compared names exactly and always
    # reported phi4-mini as missing even when it was installed.
    with patch("src.setup_check.requests.get", return_value=_mock_tags_response(
        ["phi4-mini:latest", "qwen3:8b", "gemma3:12b"]
    )):
        assert check_ollama_models() == []


def test_check_ollama_models_reports_missing_model():
    with patch("src.setup_check.requests.get", return_value=_mock_tags_response(["qwen3:8b", "gemma3:12b"])):
        problems = check_ollama_models()

    assert len(problems) == 1
    assert "phi4-mini" in problems[0]


def test_check_ollama_models_reports_unreachable_server():
    import requests

    with patch("src.setup_check.requests.get", side_effect=requests.ConnectionError):
        problems = check_ollama_models()

    assert len(problems) == 1
    assert "Ollama" in problems[0]
