import uuid

import streamlit as st
from langgraph.types import Command

from src.config import GENERIC_ERROR_MESSAGES, LANGUAGES, TEXT_MODEL_OPTIONS, has_voice
from src.graph import graph
from src.nodes.simplify import get_chain
from src.nodes.speech_out import play_wav, synthesize_to_wav
from src.setup_check import run_all_checks

st.set_page_config(page_title="Accessibility Assistant", page_icon="assets/icon.png", layout="centered")

st.title("Accessibility Assistant")
st.caption(
    "Everything runs locally on this computer using open-source models. "
    "Nothing is sent to the cloud."
)

setup_problems = run_all_checks()
if setup_problems:
    st.warning("Before you can use this, a few things need to be set up:")
    for problem in setup_problems:
        st.write(f"- {problem}")
    if st.button("I've fixed it -- check again"):
        st.rerun()
    st.stop()

language = st.selectbox("Translate into:", list(LANGUAGES.keys()), index=0)
model_choice = st.radio(
    "Speed:", list(TEXT_MODEL_OPTIONS.keys()), index=0, horizontal=True,
    help="Fast is quicker; higher quality may explain more clearly but takes longer.",
)
text_model = TEXT_MODEL_OPTIONS[model_choice]

if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None
if "info" not in st.session_state:
    st.session_state.info = None
if "history" not in st.session_state:
    st.session_state.history = []
if "thread_id" not in st.session_state:
    # Ties every graph.invoke() in this browser session to the same
    # in-memory checkpointer thread, so the graph remembers earlier turns.
    st.session_state.thread_id = str(uuid.uuid4())
if "pending_confirmation" not in st.session_state:
    # Set when the graph pauses on a human-in-the-loop gate (currently just
    # confirm_screen_capture_node) -- holds the message to show, until the
    # user picks Yes/Cancel and we resume the graph with that answer.
    st.session_state.pending_confirmation = None
    st.session_state.pending_request_summary = None

graph_config = {"configurable": {"thread_id": st.session_state.thread_id}}


def record_history(request_summary: str, response_text: str) -> None:
    st.session_state.history.append({
        "request": request_summary,
        "response": response_text,
        "language": language,
    })


def _handle_graph_output(out: dict, request_summary: str) -> None:
    if out.get("__interrupt__"):
        st.session_state.pending_confirmation = out["__interrupt__"][0].value.get("message", "Continue?")
        st.session_state.pending_request_summary = request_summary
        return

    st.session_state.pending_confirmation = None
    st.session_state.pending_request_summary = None

    if out.get("error"):
        st.session_state.error = out["error"]
    elif out.get("info"):
        st.session_state.info = out["info"]
    else:
        st.session_state.result = out
        record_history(request_summary, out["simplified_text"])


def run_graph(initial_state: dict, request_summary: str) -> None:
    st.session_state.error = None
    st.session_state.info = None
    st.session_state.result = None
    try:
        out = graph.invoke(initial_state, config=graph_config)
    except Exception as exc:
        print(f"[app] graph.invoke failed: {exc}")
        st.session_state.error = GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])
        return
    _handle_graph_output(out, request_summary)


def resume_graph(confirmed: bool) -> None:
    request_summary = st.session_state.pending_request_summary
    st.session_state.error = None
    st.session_state.info = None
    try:
        out = graph.invoke(Command(resume=confirmed), config=graph_config)
    except Exception as exc:
        print(f"[app] graph resume failed: {exc}")
        st.session_state.error = GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])
        st.session_state.pending_confirmation = None
        return
    _handle_graph_output(out, request_summary)


tab_text, tab_voice, tab_screen = st.tabs(["Type", "Listen to me", "Read my screen"])

with tab_text:
    text = st.text_area("Paste or type the confusing text here:")
    if st.button("Explain this", key="explain_text") and text.strip():
        st.session_state.error = None
        st.session_state.result = None
        placeholder = st.empty()
        try:
            # Stream tokens live instead of waiting for the full response.
            full_text = placeholder.write_stream(
                get_chain(text_model).stream({"language": language, "source_text": text})
            )
        except Exception as exc:
            print(f"[app] simplify streaming failed: {exc}")
            st.session_state.error = GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])
        else:
            placeholder.empty()
            audio_path = synthesize_to_wav(full_text, language) if has_voice(language) else None
            st.session_state.result = {"simplified_text": full_text, "audio_path": audio_path}
            record_history(text, full_text)

with tab_voice:
    st.write("Click the button, then speak for about 6 seconds.")
    if st.button("Start listening", key="record_voice"):
        with st.spinner("Listening, then translating..."):
            run_graph({
                "record_voice": True,
                "target_language": language,
                "text_model": text_model,
                "speak_output": True,
            }, request_summary="(spoken request)")

with tab_screen:
    st.write("Reads whatever is currently shown on this screen.")
    if st.session_state.pending_confirmation:
        # Human-in-the-loop gate: capturing the screen reads everything
        # currently visible, not just the document the user means to
        # share, so the graph paused (confirm_screen_capture_node) and is
        # waiting for an explicit Yes/Cancel before capture_screen_node runs.
        st.warning(st.session_state.pending_confirmation)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, continue", key="confirm_capture_yes"):
                with st.spinner("Looking at your screen..."):
                    resume_graph(True)
                st.rerun()
        with col_no:
            if st.button("Cancel", key="confirm_capture_no"):
                resume_graph(False)
                st.rerun()
    elif st.button("Read my screen", key="read_screen"):
        with st.spinner("Checking..."):
            run_graph({
                "capture_screen": True,
                "target_language": language,
                "text_model": text_model,
                "speak_output": True,
            }, request_summary="(screen reading)")
        st.rerun()

st.divider()

if st.session_state.error:
    st.error(st.session_state.error)

if st.session_state.info:
    st.info(st.session_state.info)

if st.session_state.result:
    st.subheader("Plain-language explanation")
    st.write(st.session_state.result["simplified_text"])

    audio_path = st.session_state.result.get("audio_path")
    if audio_path:
        st.audio(audio_path)
        if st.button("Read this aloud again"):
            play_wav(audio_path)

if st.session_state.history:
    with st.sidebar:
        st.subheader("Earlier this session")
        for turn in reversed(st.session_state.history[:-1] if st.session_state.result else st.session_state.history):
            with st.expander(f"{turn['language']}: {turn['request'][:40]}"):
                st.write(turn["response"])
