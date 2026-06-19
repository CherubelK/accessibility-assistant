from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.nodes.capture_screen import capture_screen_node, confirm_screen_capture_node
from src.nodes.read_screen import read_screen_node
from src.nodes.simplify import simplify_node
from src.nodes.speech_in import speech_in_node
from src.nodes.speech_out import speech_out_node
from src.routing import route_after_confirm, route_after_simplify, route_start, route_unless_error
from src.state import AssistantState

builder = StateGraph(AssistantState)
builder.add_node("confirm_screen_capture", confirm_screen_capture_node)
builder.add_node("capture_screen", capture_screen_node)
builder.add_node("read_screen", read_screen_node)
builder.add_node("speech_in", speech_in_node)
builder.add_node("simplify", simplify_node)
builder.add_node("speech_out", speech_out_node)

builder.add_conditional_edges(
    START, route_start, ["confirm_screen_capture", "read_screen", "speech_in", "simplify"]
)
builder.add_conditional_edges("confirm_screen_capture", route_after_confirm, ["capture_screen", END])
builder.add_conditional_edges("capture_screen", route_unless_error("read_screen"), ["read_screen", END])
builder.add_conditional_edges("read_screen", route_unless_error("simplify"), ["simplify", END])
builder.add_conditional_edges("speech_in", route_unless_error("simplify"), ["simplify", END])
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
