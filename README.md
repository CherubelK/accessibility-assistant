# Accessibility Assistant

A local-first assistant that reads, simplifies, and translates official text
and screens for elders and immigrants -- by text and voice, in 10 languages.
Everything runs on your own machine using open-source models. Nothing is
sent to the cloud.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full phased build spec and
[ARCHITECTURE.md](ARCHITECTURE.md) for a diagram of how the pieces fit
together.

## Setup

1. Install [Ollama](https://ollama.com) and pull the models:
   ```
   ollama pull phi4-mini
   ollama pull qwen3:8b
   ollama pull gemma3:12b
   ```
2. Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   (used alongside the vision model for exact text extraction).
3. Create a virtual environment and install Python dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
4. Download the Piper voice models (one-time, ~600MB for all 10 languages):
   ```
   bash models/download_voices.sh
   ```
5. Copy `.env.example` to `.env` if you want to override any defaults.

## Run

```
.venv\Scripts\python.exe -m streamlit run src\app.py
```

Opens at `http://localhost:8501` (bound to localhost only). Three tabs:
type text, speak into the mic, or read whatever's on your screen -- pick a
target language and get a plain-language explanation back, spoken aloud.

### As a desktop window

```
.venv\Scripts\python.exe -m src.desktop
```

Runs the same homepage in a native window instead of a browser tab --
the first step toward a downloadable desktop app.

## Supported languages

Spanish, Chinese, Vietnamese, Arabic, Russian, French, Portuguese, Hindi,
Urdu, Persian, and English (text-only -- no Piper voice configured for it).

## Tests

```
.venv\Scripts\python.exe -m pytest tests/
```

Tests call the real local `phi4-mini` model (no mocking -- this project's
whole point is that everything actually runs locally), so they need Ollama
running and are slower than typical unit tests.

## Project layout

```
src/
  state.py            shared AssistantState passed between nodes
  config.py            model names, language/voice mapping, error messages
  graph.py              LangGraph pipeline wiring
  app.py                Streamlit homepage
  desktop.py            runs the homepage in a native window (pywebview)
  setup_check.py         pre-flight check (Ollama reachable, models/voices present)
  nodes/
    capture_screen.py    screenshot capture (mss)
    read_screen.py        vision (gemma3:12b) + OCR (Tesseract)
    simplify.py            the core simplify/translate chain
    speech_in.py            speech-to-text (faster-whisper)
    speech_out.py            text-to-speech (Piper)
models/piper/            downloaded voice models (gitignored, see download_voices.sh)
samples/                  sample text/image generator for testing without real screenshots
tests/                    pytest suite
```
