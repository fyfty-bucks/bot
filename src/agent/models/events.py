"""Event and FTS5 index models."""

import json
from datetime import datetime, timezone

import peewee
from playhouse.sqlite_ext import FTS5Model, SearchField, RowIDField


_MAX_FLATTEN_DEPTH = 20


def _flatten_values(obj: object, _depth: int = 0) -> str:
    """Extract searchable text from nested structures for FTS5 index.

    Skips None and booleans to avoid index noise.
    Numbers are kept (version strings, amounts are useful for search).
    Stops recursing at _MAX_FLATTEN_DEPTH to prevent stack overflow.
    """
    if _depth >= _MAX_FLATTEN_DEPTH:
        return ""
    if obj is None or isinstance(obj, bool):
        return ""
    if isinstance(obj, dict):
        parts = [_flatten_values(v, _depth + 1) for v in obj.values()]
        return " ".join(p for p in parts if p)
    if isinstance(obj, (list, tuple)):
        parts = [_flatten_values(v, _depth + 1) for v in obj]
        return " ".join(p for p in parts if p)
    return str(obj)


class Event(peewee.Model):
    """Core event-sourced log. Every agent action becomes an event."""

    event_type = peewee.CharField(max_length=50, index=True)
    payload = peewee.TextField(default="{}")
    created_at = peewee.DateTimeField(
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    class Meta:
        table_name = "events"

    def get_payload(self) -> dict:
        """Deserialize payload JSON."""
        return json.loads(self.payload)

    @classmethod
    def log(cls, event_type: str, payload: dict) -> "Event":
        """Create event and sync to FTS5 index atomically."""
        db = cls._meta.database
        with db.atomic():
            event = cls.create(
                event_type=event_type,
                payload=json.dumps(payload),
            )
            text = _flatten_values(payload)
            EventIndex.insert({
                EventIndex.rowid: event.id,
                EventIndex.text: text,
                EventIndex.event_type: event_type,
            }).execute()
        return event


class EventIndex(FTS5Model):
    """FTS5 full-text search index over events."""

    rowid = RowIDField()
    text = SearchField()
    event_type = SearchField(unindexed=True)

    class Meta:
        table_name = "event_index"
        options = {"tokenize": "porter unicode61"}
