from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.nodes.capture_screen import capture_screen_node
from src.nodes.read_screen import read_screen_node
from src.nodes.simplify import simplify_node
from src.nodes.speech_in import speech_in_node
from src.nodes.speech_out import speech_out_node
from src.state import AssistantState


def route_start(state: AssistantState) -> str:
    """Inputs converge on `simplify` (see PROJECT_PLAN.md diagram): a
    screenshot (already provided or to be captured) goes through vision/OCR
    first; a mic request goes through speech-to-text first; plain text
    requests go straight to simplify."""
    if state.get("screenshot_path"):
        return "read_screen"
    if state.get("capture_screen"):
        return "capture_screen"
    if state.get("record_voice"):
        return "speech_in"
    return "simplify"


def route_after_simplify(state: AssistantState) -> str:
    if state.get("speak_output"):
        return "speech_out"
    return END


builder = StateGraph(AssistantState)
builder.add_node("capture_screen", capture_screen_node)
builder.add_node("read_screen", read_screen_node)
builder.add_node("speech_in", speech_in_node)
builder.add_node("simplify", simplify_node)
builder.add_node("speech_out", speech_out_node)

builder.add_conditional_edges(
    START, route_start, ["capture_screen", "read_screen", "speech_in", "simplify"]
)
builder.add_edge("capture_screen", "read_screen")
builder.add_edge("read_screen", "simplify")
builder.add_edge("speech_in", "simplify")
builder.add_conditional_edges("simplify", route_after_simplify, ["speech_out", END])
builder.add_edge("speech_out", END)

# A checkpointer lets a session remember earlier turns: invoke() calls that
# share a thread_id (see config below) read/write the same persisted state.
# In-memory only -- nothing written to disk, consistent with the local-only,
# nothing-persists-after-close design.
graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    sample_text = (
        "Your application for benefits has been received. To avoid a lapse in "
        "coverage, you must submit Form RRB-1099 and proof of income within 30 "
        "days of the date on this notice. Failure to respond may result in "
        "termination of benefits."
    )

    config = {"configurable": {"thread_id": "demo"}}
    out = graph.invoke(
        {"raw_screen_text": sample_text, "target_language": "Spanish"},
        config=config,
    )
    print("\nFinal simplified_text:\n", out["simplified_text"])
