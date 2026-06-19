"""Routing decisions for the graph, kept separate from src/graph.py so they
can be unit-tested without importing every node's (heavy) dependencies."""

from langgraph.graph import END

from src.state import AssistantState


def route_start(state: AssistantState) -> str:
    """Inputs converge on `simplify` (see PROJECT_PLAN.md diagram): a
    screenshot already provided (e.g. in tests) skips straight to
    vision/OCR; one to be freshly captured goes through a human-in-the-loop
    confirmation gate first (capturing the live screen reads everything
    visible, not just the document the user means to share); a mic request
    goes through speech-to-text first; plain text requests go straight to
    simplify."""
    if state.get("screenshot_path"):
        return "read_screen"
    if state.get("capture_screen"):
        return "confirm_screen_capture"
    if state.get("record_voice"):
        return "speech_in"
    return "simplify"


def route_after_confirm(state: AssistantState) -> str:
    return "capture_screen" if state.get("capture_confirmed") else END


def route_after_simplify(state: AssistantState) -> str:
    if state.get("error"):
        return END
    if state.get("speak_output"):
        return "speech_out"
    return END


def route_unless_error(next_node: str):
    """A node that fails sets state['error'] instead of raising (so it shows
    a translated message instead of a crash). If it did, stop here rather
    than feeding a missing/partial result into the next node."""
    def _route(state: AssistantState) -> str:
        return END if state.get("error") else next_node
    return _route
