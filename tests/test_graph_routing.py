"""Tests for the routing functions in src/routing.py. Pure logic, no model
calls -- these decide which node runs next based on state, they don't run
any node themselves.
"""

from langgraph.graph import END

from src.routing import route_after_confirm, route_after_simplify, route_start, route_unless_error


def test_route_start_screenshot_already_provided_goes_to_read_screen():
    assert route_start({"screenshot_path": "x.png"}) == "read_screen"


def test_route_start_capture_screen_flag_goes_to_confirmation_gate():
    assert route_start({"capture_screen": True}) == "confirm_screen_capture"


def test_route_start_record_voice_flag_goes_to_speech_in():
    assert route_start({"record_voice": True}) == "speech_in"


def test_route_start_plain_text_goes_straight_to_simplify():
    assert route_start({"user_request": "hello"}) == "simplify"


def test_route_after_simplify_speaks_when_requested():
    assert route_after_simplify({"speak_output": True}) == "speech_out"


def test_route_after_simplify_skips_speech_on_error_even_if_requested():
    assert route_after_simplify({"speak_output": True, "error": "oops"}) == END


def test_route_after_simplify_ends_by_default():
    assert route_after_simplify({}) == END


def test_route_unless_error_continues_on_success():
    route = route_unless_error("next_node")
    assert route({}) == "next_node"


def test_route_unless_error_stops_on_error():
    route = route_unless_error("next_node")
    assert route({"error": "oops"}) == END


def test_route_after_confirm_proceeds_when_confirmed():
    assert route_after_confirm({"capture_confirmed": True}) == "capture_screen"


def test_route_after_confirm_stops_when_declined():
    assert route_after_confirm({"capture_confirmed": False}) == END


def test_route_after_confirm_stops_when_unset():
    assert route_after_confirm({}) == END
