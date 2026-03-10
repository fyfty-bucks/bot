"""Tests for core agent loop — receive, route, execute with HandleResult."""

import json

from src.agent.core import AgentCore, HandleResult
from src.agent.models.events import Event


def _ok_handler(event_data: dict) -> dict:
    return {"status": "ok", "received": event_data}


def _fail_handler(event_data: dict) -> dict:
    raise RuntimeError("handler exploded")


def _none_handler(event_data: dict) -> None:
    return None


def test_receive_creates_event(test_db) -> None:
    """receive() stores an incoming event in the database."""
    core = AgentCore(test_db)
    event = core.receive("telegram", {"text": "hello"})

    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "telegram"
    assert json.loads(loaded.payload) == {"text": "hello"}


def test_execute_calls_handler(test_db) -> None:
    """execute() returns HandleResult with handler's output."""
    core = AgentCore(test_db)
    core.registry.register("echo", _ok_handler)

    event = core.receive("echo", {"msg": "test"})
    hr = core.execute(event)

    assert isinstance(hr, HandleResult)
    assert hr.handled is True
    assert hr.result["status"] == "ok"
    assert hr.error is None


def test_execute_stores_result(test_db) -> None:
    """Handler result is stored as a new event."""
    core = AgentCore(test_db)
    core.registry.register("echo", _ok_handler)

    event = core.receive("echo", {"msg": "test"})
    core.execute(event)

    result_events = list(
        Event.select().where(Event.event_type == "handler_result")
    )
    assert len(result_events) == 1
    payload = json.loads(result_events[0].payload)
    assert payload["status"] == "ok"


def test_execute_handles_error(test_db) -> None:
    """Handler exception is caught, stored, and returned in HandleResult."""
    core = AgentCore(test_db)
    core.registry.register("boom", _fail_handler)

    event = core.receive("boom", {})
    hr = core.execute(event)

    assert hr.handled is True
    assert hr.result is None
    assert "handler exploded" in hr.error

    error_events = list(
        Event.select().where(Event.event_type == "error")
    )
    assert len(error_events) == 1


def test_execute_no_handler_returns_unhandled(test_db) -> None:
    """Unknown event type returns HandleResult(handled=False)."""
    core = AgentCore(test_db)

    event = core.receive("unknown_type", {"data": 1})
    hr = core.execute(event)

    assert isinstance(hr, HandleResult)
    assert hr.handled is False
    assert hr.result is None
    assert hr.error is None


def test_execute_handler_returns_none(test_db) -> None:
    """Handler returning None gives HandleResult(handled=True, result=None)."""
    core = AgentCore(test_db)
    core.registry.register("silent", _none_handler)

    event = core.receive("silent", {})
    hr = core.execute(event)

    assert hr.handled is True
    assert hr.result is None
    assert hr.error is None


def test_receive_is_atomic(test_db) -> None:
    """receive() wraps DB write in a transaction."""
    core = AgentCore(test_db)
    event = core.receive("atomic_test", {"key": "val"})

    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "atomic_test"


def test_full_cycle(test_db) -> None:
    """Full cycle: receive -> execute -> both events in DB."""
    core = AgentCore(test_db)
    core.registry.register("ping", lambda d: {"pong": True})

    event = core.receive("ping", {"from": "cli"})
    hr = core.execute(event)

    assert hr.handled is True
    assert hr.result == {"pong": True}

    all_events = list(Event.select().order_by(Event.id))
    assert len(all_events) == 2

    assert all_events[0].event_type == "ping"
    assert json.loads(all_events[0].payload) == {"from": "cli"}

    assert all_events[1].event_type == "handler_result"
    result = json.loads(all_events[1].payload)
    assert result["pong"] is True


# --- Edge cases ---


def test_receive_empty_data(test_db) -> None:
    """receive() with empty dict stores valid event."""
    core = AgentCore(test_db)
    event = core.receive("empty", {})

    loaded = Event.get_by_id(event.id)
    assert json.loads(loaded.payload) == {}


def test_receive_unicode_data(test_db) -> None:
    """receive() with unicode data round-trips correctly."""
    core = AgentCore(test_db)
    data = {"msg": "Привет", "emoji": "🤖"}
    event = core.receive("unicode", data)

    loaded = Event.get_by_id(event.id)
    assert json.loads(loaded.payload) == data


def test_receive_large_data(test_db) -> None:
    """receive() with large payload stores correctly."""
    core = AgentCore(test_db)
    data = {"items": [{"id": i, "v": "x" * 100} for i in range(100)]}
    event = core.receive("large", data)

    loaded = Event.get_by_id(event.id)
    assert json.loads(loaded.payload) == data
