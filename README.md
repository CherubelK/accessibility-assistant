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
6. **Set `OLLAMA_MAX_LOADED_MODELS=1`** as a system/user environment
   variable, then restart Ollama. Without this, Ollama will keep multiple
   models resident in RAM simultaneously if there's room (e.g. `phi4-mini` +
   `gemma3:12b` together still fit under 16GB), which causes severe slowdown
   from memory pressure -- observed 84s for a request that takes 17s with
   only one model loaded. This setting makes Ollama strictly swap one model
   out before loading another, matching this project's "one model at a
   time" design assumption (see PROJECT_PLAN.md).

## Run

```
.venv\Scripts\python.exe -m streamlit run src\app.py
```

Opens at `http://localhost:8501` (bound to localhost only). Three tabs:
type text, speak into the mic, or read whatever's on your screen -- pick a
target language and a speed ("Fast" = `phi4-mini`, "Higher quality" =
`qwen3:8b`), and get a plain-language explanation back, spoken aloud.

### As a desktop window

```
.venv\Scripts\python.exe -m src.desktop
```

Runs the same homepage in a native window instead of a browser tab --
the first step toward a downloadable desktop app.

### As a standalone .exe (no Python install required)

```
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller desktop.spec --noconfirm
dist\AccessibilityAssistant\AccessibilityAssistant.exe
```

Produces `dist/AccessibilityAssistant/` -- copy that whole folder to share
it; the `.exe` inside is the entry point. It still needs Ollama installed
and running on the target machine (that part isn't bundled), but no
Python/pip/venv is required to run it.

Two non-obvious things had to be fixed to get this working (see comments in
`src/desktop.py` and `desktop.spec` for details, in case Streamlit's
internals change again in a future version):
- Streamlit loads `app.py` dynamically at runtime, not via a Python
  `import`, so PyInstaller's static analysis can't see its dependencies --
  every module `app.py` needs has to be listed explicitly as a hidden
  import in `desktop.spec`.
- Streamlit decides whether to serve its own static assets based on an
  "am I installed normally" heuristic that checks for `"site-packages"` in
  its own file path. PyInstaller relocates everything into `_internal/`,
  so that heuristic always misfires once frozen -- silently disabling the
  static file routes and returning 404 for everything, including the
  homepage itself. Fixed by explicitly forcing `global_developmentMode`
  off via `bootstrap.load_config_options()` before starting the server.

## Supported languages

Spanish, Chinese, Vietnamese, Arabic, Russian, French, Portuguese, Hindi,
Urdu, Persian, and English (text-only -- no Piper voice configured for it).

## Tests

```
.venv\Scripts\python.exe -m pytest tests/
```

Most tests call the real local `phi4-mini` model (no mocking -- this
project's whole point is that everything actually runs locally), so they
need Ollama running and are slower than typical unit tests. The ones marked
`@pytest.mark.requires_ollama` are skipped in CI (`.github/workflows/test.yml`);
everything else runs there on every push:

```
.venv\Scripts\python.exe -m pytest tests/ -m "not requires_ollama"
```

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
