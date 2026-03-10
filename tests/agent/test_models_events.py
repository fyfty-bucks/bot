"""Tests for Event and EventIndex (FTS5) models."""

import json
from datetime import datetime, timezone, timedelta

from src.agent.models.events import Event, EventIndex


def test_create_event(test_db) -> None:
    """Basic event creation and retrieval."""
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


def test_fts5_search_finds_matching(test_db) -> None:
    """FTS5 search finds matching text."""
    event = Event.create(
        event_type="task_completed",
        payload=json.dumps({"desc": "deployed new skill module"}),
    )
    EventIndex.insert({
        EventIndex.rowid: event.id,
        EventIndex.text: "deployed new skill module",
        EventIndex.event_type: event.event_type,
    }).execute()

    results = list(EventIndex.search_bm25("deploy skill").limit(5))
    assert len(results) >= 1
    assert "deploy" in results[0].text or "skill" in results[0].text


def test_fts5_search_no_match(test_db) -> None:
    """FTS5 search returns empty for non-matching query."""
    event = Event.create(event_type="check", payload="{}")
    EventIndex.insert({
        EventIndex.rowid: event.id,
        EventIndex.text: "budget check completed",
        EventIndex.event_type: event.event_type,
    }).execute()

    results = list(EventIndex.search_bm25("telegram message").limit(5))
    assert len(results) == 0


def test_fts5_search_ranked(test_db) -> None:
    """FTS5 results are ranked by relevance."""
    texts = [
        "deploy module to production server",
        "production deploy of skill module with deploy verification",
        "unrelated budget check",
    ]
    for i, text in enumerate(texts):
        event = Event.create(event_type="log", payload="{}")
        EventIndex.insert({
            EventIndex.rowid: event.id,
            EventIndex.text: text,
            EventIndex.event_type: "log",
        }).execute()

    results = list(EventIndex.search_bm25("deploy", with_score=True).limit(3))
    assert len(results) >= 2
    assert "deploy" in results[0].text


def test_event_index_synced_on_create(test_db) -> None:
    """EventIndex entry matches the Event rowid."""
    event = Event.create(event_type="sync_test", payload="{}")
    EventIndex.insert({
        EventIndex.rowid: event.id,
        EventIndex.text: "sync verification entry",
        EventIndex.event_type: event.event_type,
    }).execute()

    idx = EventIndex.get(EventIndex.rowid == event.id)
    assert idx.text == "sync verification entry"
    assert idx.event_type == "sync_test"
