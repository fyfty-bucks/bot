"""Tests for core agent loop — receive, route, execute, store."""

import json

from src.agent.core import AgentCore
from src.agent.models.events import Event


def _ok_handler(event_data: dict) -> dict:
    return {"status": "ok", "received": event_data}


def _fail_handler(event_data: dict) -> dict:
    raise RuntimeError("handler exploded")


def test_receive_creates_event(test_db) -> None:
    """receive() stores an incoming event in the database."""
    core = AgentCore(test_db)
    event = core.receive("telegram", {"text": "hello"})

    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "telegram"
    assert json.loads(loaded.payload) == {"text": "hello"}


def test_execute_calls_handler(test_db) -> None:
    """execute() calls the registered handler for the event type."""
    core = AgentCore(test_db)
    core.registry.register("echo", _ok_handler)

    event = core.receive("echo", {"msg": "test"})
    result = core.execute(event)

    assert result is not None
    assert result["status"] == "ok"


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
    """Handler exception is caught and stored, not re-raised."""
    core = AgentCore(test_db)
    core.registry.register("boom", _fail_handler)

    event = core.receive("boom", {})
    result = core.execute(event)

    assert result is None

    error_events = list(
        Event.select().where(Event.event_type == "error")
    )
    assert len(error_events) == 1
    payload = json.loads(error_events[0].payload)
    assert "handler exploded" in payload["error"]


def test_full_cycle(test_db) -> None:
    """Full cycle: receive -> execute -> both events in DB."""
    core = AgentCore(test_db)
    core.registry.register("ping", lambda d: {"pong": True})

    event = core.receive("ping", {"from": "cli"})
    core.execute(event)

    all_events = list(Event.select().order_by(Event.id))
    assert len(all_events) == 2

    assert all_events[0].event_type == "ping"
    assert json.loads(all_events[0].payload) == {"from": "cli"}

    assert all_events[1].event_type == "handler_result"
    result = json.loads(all_events[1].payload)
    assert result["pong"] is True
