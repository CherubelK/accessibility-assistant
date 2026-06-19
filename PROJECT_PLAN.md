# Accessibility Assistant — Project Plan

A local-first, privacy-preserving assistant that helps elders and immigrants
navigate government and official systems. It reads what is on screen, explains
it in plain language, translates it into the user's native language, and
responds by both **text and voice**. Everything runs locally — no API keys, no
cloud, no data leaving the machine.

This document is the working spec for building the app with **Claude Code in
VS Code**. It is also a structured learning path: the project doubles as a way
to learn LangChain and LangGraph from zero. Build it in the order given. Each
phase produces something that runs on its own.

---

## How to use this file with Claude Code

- This file is the source of truth. When asking Claude Code to do something,
  point it at the relevant phase (e.g. "implement Phase 2, the LangGraph
  pipeline").
- Work **one phase at a time**. Do not let scope jump ahead — each phase has a
  checkpoint that must pass before moving on.
- After each phase, run the checkpoint manually and confirm it works before
  asking Claude Code to continue.
- Keep this file open in the editor so Claude Code keeps the full plan in
  context.
- When something doesn't work, paste the actual error back rather than
  describing it.

---

## Why this design

- **Local-first for privacy.** Screenshots of someone's benefits forms, medical
  letters, or immigration paperwork must never leave their device. Local models
  via Ollama make that guarantee structural, not a promise.
- **Sequential, not simultaneous.** The target hardware (see below) is CPU-only
  with limited RAM. Models run one at a time, handing off through shared state.
  This is a pipeline, which is exactly what LangGraph expresses well.
- **Layered build.** Each phase adds one capability and remains independently
  runnable, so you are never stuck with a half-built thing that won't start.

---

## Target hardware constraints

The reference machine is a typical mid-range laptop:

- 11th-gen Intel i5, **CPU-only** (integrated Iris Xe, no dedicated GPU)
- **16 GB RAM**
- Ample disk (hundreds of GB free)

Implications that shape every decision:

- Only **one model resident in RAM at a time.** Ollama loads/unloads on switch.
- Practical model ceiling is **7B–14B**. Larger frontier models (Qwen 235B,
  GLM, Kimi) are out of scope — they need multi-GPU rigs.
- Responses stream at reading pace on CPU. This is normal, not a bug.
- Vision and speech are heavier; expect them to be the slowest nodes.

---

## Tech stack

| Concern | Tool | Notes |
|---|---|---|
| Model runtime | **Ollama** | Serves local models on `localhost:11434` |
| Orchestration | **LangGraph / LangChain** | Pipeline as a state graph |
| Text model | **Qwen 3 8B** (`qwen3:8b`) | Strong multilingual summarize/translate |
| Fast/iteration model | **Phi-4-mini** (`phi4-mini`) | Snappy for development loops |
| Vision model | **Gemma 3 12B** (`gemma3:12b`) | Reads screenshots (image → text) |
| OCR (optional, recommended) | **Tesseract** (`pytesseract`) | Exact text extraction to pair with vision |
| Screenshot capture | **mss** or **Pillow ImageGrab** | Grab the active screen |
| Voice in (STT) | **faster-whisper** | Local speech-to-text |
| Voice out (TTS) | **Piper** | Local, natural multilingual speech |
| Language | **Python 3.10+** | 3.13 works; pin versions |

> **Version pinning matters.** LangChain and LangGraph ship breaking changes
> often. Pin everything in `requirements.txt` and check the changelog when a
> tutorial's syntax doesn't match. Treat the official docs and LangChain Academy
> as the source of truth over blog posts.

---

## Models to pull (Ollama)

Run these once. You don't need all of them before starting — phases 1–2 only
need a text model.

```bash
ollama pull phi4-mini      # ~2.5 GB - fastest, for dev iteration
ollama pull qwen3:8b       # ~5 GB   - main text/translation model
ollama pull gemma3:12b     # ~8 GB   - vision (needed from Phase 3)
```

Verify a model responds before writing code:

```bash
ollama run phi4-mini "hola"
```

---

## Repository layout (target)

This is where the project is heading. Build it up file by file across phases —
don't scaffold everything empty on day one.

```
accessibility-assistant/
├─ PROJECT_PLAN.md            # this file
├─ requirements.txt           # pinned deps
├─ .env.example               # config template (no secrets — local only)
├─ .gitignore
├─ src/
│  ├─ __init__.py
│  ├─ config.py               # model names, language settings
│  ├─ state.py                # the shared AssistantState (Phase 2+)
│  ├─ models.py               # model factory / swapping
│  ├─ nodes/
│  │  ├─ __init__.py
│  │  ├─ capture_screen.py    # screenshot (Phase 3)
│  │  ├─ read_screen.py       # vision + OCR (Phase 3)
│  │  ├─ simplify.py          # summarize + translate (Phase 1→2)
│  │  ├─ speech_in.py         # Whisper STT (Phase 4)
│  │  └─ speech_out.py        # Piper TTS (Phase 4)
│  ├─ graph.py                # LangGraph wiring (Phase 2+)
│  └─ app.py                  # entry point / simple UI (Phase 5)
├─ tests/
│  └─ test_simplify.py
└─ samples/                   # sample official texts & screenshots for testing
```

---

## Core architecture

The app is a LangGraph pipeline. Two input branches (voice/text request, and a
screenshot) converge on a single simplify-and-translate step, then deliver the
result as both text and voice.

```
[Capture request]          [Capture screen]
 voice (Whisper) / text     screenshot
        │                        │
        ▼                        ▼
 [Hold user request]      [Vision model reads screen]
        │                   Gemma 3 (image → text)
        │                        │
        └──────────┬─────────────┘
                   ▼
        [Summarize & translate]
         Qwen 3 → native language
                   │
                   ▼
            [Deliver result]
       text on screen + voice (Piper)
```

The **state** object flows through every node, accumulating data: the user's
request, the raw screen text, the simplified translation, and the audio output
path. Each node reads what it needs and writes its result back.

---

## The shared state

From Phase 2 onward, every node reads and writes a single typed state object.
Define it once in `src/state.py`:

```python
from typing import TypedDict, Optional

class AssistantState(TypedDict, total=False):
    # input
    user_request: str          # what the person asked (typed or transcribed)
    target_language: str       # e.g. "Spanish"
    screenshot_path: Optional[str]

    # intermediate
    raw_screen_text: str       # vision + OCR output
    ocr_text: Optional[str]    # exact text from Tesseract, if used

    # output
    simplified_text: str       # plain-language translation
    audio_path: Optional[str]  # path to spoken-version audio file

    # control / safety
    needs_confirmation: bool   # gate before any consequential action
    error: Optional[str]
```

`total=False` lets nodes fill fields incrementally as the pipeline progresses.

---

## Build phases

Each phase: **what to build**, **why**, and a **checkpoint** that must pass
before continuing.

### Phase 0 — Environment

**Build**
1. Create and activate a virtual environment.
2. `pip install langchain langgraph langchain-ollama python-dotenv` and freeze
   to `requirements.txt`.
3. Confirm Ollama is installed and at least one model responds.

**Checkpoint:** `ollama run phi4-mini "hello"` returns text, and
`python -c "import langchain, langgraph, langchain_ollama"` runs without error.

---

### Phase 1 — Text simplify & translate (a simple chain)

**Build** the seed of the whole app: a script that takes a block of confusing
official text and returns a plain-language summary translated into the target
language, using one local model.

Core pattern — the LCEL chain `prompt | llm | parser`:

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOllama(model="phi4-mini", temperature=0.2)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You help elders and immigrants understand confusing government and "
     "official text. Explain what the text means in simple, calm, plain "
     "language a non-expert can follow. Do not add information that is not in "
     "the text. If an action or deadline is required, state it clearly. "
     "Respond ONLY in {language}."),
    ("human", "Here is the text to explain:\n\n{source_text}"),
])

chain = prompt | llm | StrOutputParser()

result = chain.invoke({"language": "Spanish", "source_text": SAMPLE})
print(result)
```

**Why:** `prompt | llm | parser` is LangChain's core composition unit. Every
later layer is made of pieces shaped like this. The model is one swappable line
— change `"phi4-mini"` to `"qwen3:8b"` and rerun to feel the quality/speed
tradeoff. The guardrail "do not add information that is not in the text" is a
**safety** requirement here: an invented deadline could cause real harm.

**Checkpoint:** Running the script returns a calm, accurate Spanish explanation
that preserves any deadline/action and invents nothing. Swap in a second model
and compare output.

---

### Phase 2 — Rebuild as a LangGraph pipeline

**Build** the same simplify/translate logic, but as a graph: define
`AssistantState`, wrap the logic in a node function, wire it into a
`StateGraph`, compile, and invoke.

```python
from langgraph.graph import StateGraph, START, END
from src.state import AssistantState

def simplify_node(state: AssistantState) -> dict:
    text = state["raw_screen_text"]      # or user-supplied text for now
    lang = state["target_language"]
    simplified = chain.invoke({"language": lang, "source_text": text})
    return {"simplified_text": simplified}

builder = StateGraph(AssistantState)
builder.add_node("simplify", simplify_node)
builder.add_edge(START, "simplify")
builder.add_edge("simplify", END)
graph = builder.compile()

out = graph.invoke({
    "raw_screen_text": SAMPLE,
    "target_language": "Spanish",
})
print(out["simplified_text"])
```

**Why:** This is the shift from a linear chain to a graph. Nodes are functions
that read and update shared state. **Print the state at the start and end of
every node while learning** — seeing how data flows is the single most
important habit for understanding LangGraph.

**Checkpoint:** The graph produces the same quality output as Phase 1, and you
can explain — in your own words — what the state, the node, and the edges are.

---

### Phase 3 — Add the screen-reading node (vision + OCR)

**Build**
1. `capture_screen.py` — grab a screenshot (use `mss`), save to a temp path,
   write `screenshot_path` to state.
2. `read_screen.py` — feed the image to **Gemma 3** for a layout-aware reading,
   and optionally run **Tesseract** for exact text. Combine into
   `raw_screen_text`.
3. Add both as nodes upstream of `simplify`. The vision/OCR result flows into
   the existing simplify node.

Passing an image to a vision model via Ollama (sketch):

```python
from langchain_ollama import ChatOllama

vision = ChatOllama(model="gemma3:12b")

def read_screen_node(state: AssistantState) -> dict:
    msg = {
        "role": "user",
        "content": "Read this screen and describe what it says and what the "
                   "user is being asked to do.",
        "images": [state["screenshot_path"]],
    }
    result = vision.invoke([msg])
    return {"raw_screen_text": result.content}
```

**Why:** This is "multiple models working together" — vision hands off to text,
through state. Vision models read clean screen text well but struggle with tiny
fonts and clutter; pairing with OCR (exact text) plus vision (layout/context)
is more robust for real government pages.

**Checkpoint:** Screenshot a real (or sample) official page; the pipeline
returns an accurate plain-language Spanish explanation of what's on it,
including any required action.

---

### Phase 4 — Add voice (Whisper in, Piper out)

**Build**
1. `speech_in.py` — record mic audio, transcribe with **faster-whisper**, write
   `user_request`. Make this an optional entry path (text still works).
2. `speech_out.py` — synthesize `simplified_text` with **Piper** in the target
   language, save audio, write `audio_path`, and play it.
3. Wire speech-in as an alternative input node and speech-out as the final node.

**Why:** Saved for last deliberately — STT/TTS are separate libraries (not
LangGraph) and the fiddliest part on Windows (mic drivers, audio backends). The
whole app is useful as text-only before this; adding voice last means a driver
issue never blocks the core build.

**Watch out:** TTS voice quality and availability varies by language. Test with
the **actual languages your users speak**, especially less-resourced ones where
both translation and speech quality drop — precisely the communities this tool
serves.

**Checkpoint:** Speak a request, point at a screen; the app speaks back a
plain-language explanation in the target language and shows the same text.

---

### Phase 5 — Human-in-the-loop, UI, and hardening

**Build**
1. **Human-in-the-loop:** add a checkpoint/interrupt before any consequential
   action (e.g. anything that would submit a form), so the app pauses and asks
   for confirmation. Use `needs_confirmation` in state.
2. **Memory:** add a checkpointer so a session remembers earlier turns.
3. **Streaming:** stream the simplify node so the user sees text appear live.
4. **Simple UI:** a minimal interface (start with a CLI or a small local web UI)
   with large text, high contrast, and a "read this aloud again" button.
5. **Error handling:** every node should fail gracefully and explain, in the
   user's language, when something went wrong rather than crashing.

**Why:** These turn a working pipeline into something an elder or non-technical
user could actually operate safely. The confirmation gate matters most — the
app should never take an irreversible action on someone's behalf without
explicit approval.

**Checkpoint:** A full end-to-end run from voice or screen input to spoken +
written output, with a confirmation pause before any sensitive step, memory
across turns, and graceful handling of at least one induced failure. Write a
short README describing the architecture in your own words — if you can explain
it, you've learned it.

---

## Progress tracker

| Phase | Deliverable | Done |
|---|---|---|
| 0 | Environment + models responding | ☑ |
| 1 | Text simplify & translate chain | ☑ |
| 2 | Same logic as a LangGraph pipeline | ☑ |
| 3 | Screenshot + vision/OCR reading node | ☑ |
| 4 | Voice in (Whisper) + voice out (Piper) | ☑ |
| 5 | Human-in-the-loop, memory, streaming, UI | ☑ (memory + streaming + UI done; no HITL gate yet -- no consequential/submit action exists to guard) |

---

## Design principles to hold throughout

- **Never invent facts.** For an accessibility tool, a hallucinated deadline or
  instruction can cause real harm. Prompts must forbid adding information not
  present in the source, and the app should say when it is unsure.
- **Privacy is structural.** Nothing leaves the device. No telemetry, no cloud
  calls. Keep it that way.
- **Confirm before acting.** The app explains and assists; it does not take
  consequential actions without explicit user approval.
- **Test in the real languages.** Quality varies by language. Validate with the
  languages and document types your actual users face.
- **One model at a time.** Respect the hardware. Let Ollama load/unload; don't
  try to hold vision + text + speech models in RAM simultaneously.
- **Swap models freely.** Model choice is one line. Iterate fast on `phi4-mini`,
  validate quality on `qwen3:8b` / `gemma3:12b`.

---

## Learning path mapping

This project is also the LangChain/LangGraph curriculum, compressed:

- **Phase 1** teaches chains, prompt templates, output parsers, LCEL, and model
  swapping.
- **Phase 2** teaches state, nodes, edges, and the graph mental model.
- **Phase 3** teaches multi-node pipelines, model hand-off, and multimodal
  input.
- **Phase 4** teaches integrating non-LLM tools into a graph.
- **Phase 5** teaches persistence/memory, human-in-the-loop, streaming, and
  shipping.

Build in order, run every checkpoint, and code every concept the moment you
read it.
