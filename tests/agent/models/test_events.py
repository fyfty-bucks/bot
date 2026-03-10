"""Tests for Event and EventIndex — including Event.log() auto-sync."""

import json
from datetime import datetime, timezone, timedelta

from src.agent.models.events import Event, EventIndex


def test_create_event(test_db) -> None:
    """Basic event creation and retrieval via raw create()."""
    event = Event.create(
        event_type="task_completed",
        payload=json.dumps({"task": "deploy"}),
    )
    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "task_completed"
    assert json.loads(loaded.payload) == {"task": "deploy"}


def test_event_created_at_auto(test_db) -> None:
    """created_at is populated automatically."""
    event = Event.create(event_type="test", payload="{}")
    assert event.created_at is not None
    assert isinstance(event.created_at, datetime)


def test_event_payload_is_json(test_db) -> None:
    """Payload round-trips through JSON correctly."""
    data = {"cost": 0.01, "tokens": 150, "nested": {"a": 1}}
    event = Event.create(
        event_type="llm_call",
        payload=json.dumps(data),
    )
    loaded = Event.get_by_id(event.id)
    assert loaded.get_payload() == data


def test_filter_events_by_type(test_db) -> None:
    """Filter events by event_type."""
    Event.create(event_type="llm_call", payload="{}")
    Event.create(event_type="error", payload="{}")
    Event.create(event_type="task_completed", payload="{}")

    llm_events = list(Event.select().where(Event.event_type == "llm_call"))
    assert len(llm_events) == 1
    assert llm_events[0].event_type == "llm_call"


def test_filter_events_by_date_range(test_db) -> None:
    """Filter events by date range."""
    base = datetime(2026, 3, 10, tzinfo=timezone.utc)
    for i in range(5):
        Event.create(
            event_type="daily",
            payload="{}",
            created_at=base + timedelta(days=i),
        )

    start = base + timedelta(days=1)
    end = base + timedelta(days=3)
    results = list(
        Event.select().where(Event.created_at.between(start, end))
    )
    assert len(results) == 3


def test_log_creates_event_and_index(test_db) -> None:
    """Event.log() creates both Event row and EventIndex entry."""
    event = Event.log("task_completed", {"desc": "deployed module"})

    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "task_completed"

    idx = EventIndex.get(EventIndex.rowid == event.id)
    assert idx.event_type == "task_completed"
    assert "deployed module" in idx.text


def test_log_searchable_via_fts5(test_db) -> None:
    """Events created via log() are immediately searchable."""
    Event.log("deploy", {"desc": "deployed new skill module"})

    results = list(EventIndex.search_bm25("deploy skill").limit(5))
    assert len(results) >= 1
    assert "deploy" in results[0].text or "skill" in results[0].text


def test_fts5_search_no_match(test_db) -> None:
    """FTS5 search returns empty for non-matching query."""
    Event.log("check", {"desc": "budget check completed"})

    results = list(EventIndex.search_bm25("telegram message").limit(5))
    assert len(results) == 0


def test_fts5_search_ranked(test_db) -> None:
    """FTS5 results are ranked by relevance."""
    texts = [
        "deploy module to production server",
        "production deploy of skill module with deploy verification",
        "unrelated budget check",
    ]
    for text in texts:
        Event.log("log", {"desc": text})

    results = list(EventIndex.search_bm25("deploy", with_score=True).limit(3))
    assert len(results) >= 2
    assert "deploy" in results[0].text


# --- Edge cases ---


def test_event_empty_payload(test_db) -> None:
    """Event with empty dict payload stores and retrieves correctly."""
    event = Event.create(event_type="empty", payload=json.dumps({}))
    loaded = Event.get_by_id(event.id)
    assert loaded.get_payload() == {}


def test_event_unicode_payload(test_db) -> None:
    """Event with unicode characters in payload round-trips correctly."""
    data = {"msg": "Привет мир", "emoji": "🤖", "jp": "日本語"}
    event = Event.create(event_type="unicode", payload=json.dumps(data))
    loaded = Event.get_by_id(event.id)
    assert loaded.get_payload() == data


def test_event_large_payload(test_db) -> None:
    """Event with ~10KB payload stores and retrieves correctly."""
    data = {"items": [{"id": i, "text": "x" * 100} for i in range(100)]}
    event = Event.create(event_type="large", payload=json.dumps(data))
    loaded = Event.get_by_id(event.id)
    assert loaded.get_payload() == data


def test_log_empty_payload(test_db) -> None:
    """Event.log() with empty dict creates event and index."""
    event = Event.log("empty", {})
    loaded = Event.get_by_id(event.id)
    assert loaded.event_type == "empty"


def test_log_unicode_payload(test_db) -> None:
    """Event.log() indexes unicode text for FTS5 search."""
    Event.log("msg", {"text": "Привет мир, это агент"})
    results = list(EventIndex.search_bm25("агент").limit(5))
    assert len(results) >= 1
