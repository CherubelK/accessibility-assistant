import uuid

import streamlit as st

from src.config import GENERIC_ERROR_MESSAGES, LANGUAGES, has_voice
from src.graph import graph
from src.nodes.simplify import chain as simplify_chain
from src.nodes.speech_out import play_wav, synthesize_to_wav

st.set_page_config(page_title="Accessibility Assistant", layout="centered")

st.title("Accessibility Assistant")
st.caption(
    "Everything runs locally on this computer using open-source models. "
    "Nothing is sent to the cloud."
)

language = st.selectbox("Translate into:", list(LANGUAGES.keys()), index=0)

if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None
if "history" not in st.session_state:
    st.session_state.history = []
if "thread_id" not in st.session_state:
    # Ties every graph.invoke() in this browser session to the same
    # in-memory checkpointer thread, so the graph remembers earlier turns.
    st.session_state.thread_id = str(uuid.uuid4())

graph_config = {"configurable": {"thread_id": st.session_state.thread_id}}


def record_history(request_summary: str, response_text: str) -> None:
    st.session_state.history.append({
        "request": request_summary,
        "response": response_text,
        "language": language,
    })


def run_graph(initial_state: dict, request_summary: str) -> None:
    st.session_state.error = None
    st.session_state.result = None
    try:
        out = graph.invoke(initial_state, config=graph_config)
    except Exception as exc:
        print(f"[app] graph.invoke failed: {exc}")
        st.session_state.error = GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])
        return

    if out.get("error"):
        st.session_state.error = out["error"]
    else:
        st.session_state.result = out
        record_history(request_summary, out["simplified_text"])


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
                simplify_chain.stream({"language": language, "source_text": text})
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
                "speak_output": True,
            }, request_summary="(spoken request)")

with tab_screen:
    st.write("Reads whatever is currently shown on this screen.")
    if st.button("Read my screen", key="read_screen"):
        with st.spinner("Looking at your screen..."):
            run_graph({
                "capture_screen": True,
                "target_language": language,
                "speak_output": True,
            }, request_summary="(screen reading)")

st.divider()

if st.session_state.error:
    st.error(st.session_state.error)

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
