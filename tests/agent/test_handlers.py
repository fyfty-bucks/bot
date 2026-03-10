"""Tests for handler registry — register, route, discover."""

from src.agent.handlers import HandlerRegistry


def _echo_handler(event_data: dict) -> dict:
    return {"echo": event_data}


def _upper_handler(event_data: dict) -> dict:
    return {"upper": str(event_data).upper()}


def test_register_handler() -> None:
    """Handler is stored in registry after register()."""
    reg = HandlerRegistry()
    reg.register("echo", _echo_handler)
    assert "echo" in reg.handlers


def test_route_to_correct_handler() -> None:
    """Event is routed to the matching handler."""
    reg = HandlerRegistry()
    reg.register("echo", _echo_handler)
    reg.register("upper", _upper_handler)

    result = reg.route("echo", {"msg": "hello"})
    assert result == {"echo": {"msg": "hello"}}


def test_unknown_event_type_returns_none() -> None:
    """Unknown event type returns None, does not raise."""
    reg = HandlerRegistry()
    reg.register("echo", _echo_handler)

    result = reg.route("unknown", {"msg": "test"})
    assert result is None


def test_handler_receives_event_data() -> None:
    """Handler receives the full event data dict."""
    received = {}

    def capture_handler(event_data: dict) -> dict:
        received.update(event_data)
        return {"ok": True}

    reg = HandlerRegistry()
    reg.register("capture", capture_handler)

    payload = {"key": "value", "count": 42}
    reg.route("capture", payload)
    assert received == payload


def test_discover_handlers_from_package(tmp_path) -> None:
    """Auto-discovery finds handler modules in a package directory."""
    pkg = tmp_path / "handlers"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")

    (pkg / "echo.py").write_text(
        'name = "echo"\n'
        'def handle(data: dict) -> dict:\n'
        '    return {"echo": data}\n'
    )
    (pkg / "ping.py").write_text(
        'name = "ping"\n'
        'def handle(data: dict) -> dict:\n'
        '    return {"pong": True}\n'
    )

    reg = HandlerRegistry()
    reg.discover(str(pkg))
    assert "echo" in reg.handlers
    assert "ping" in reg.handlers

    result = reg.route("ping", {})
    assert result == {"pong": True}
