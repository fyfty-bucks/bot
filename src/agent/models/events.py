"""Event and FTS5 index models."""

import json
from datetime import datetime, timezone

import peewee
from playhouse.sqlite_ext import FTS5Model, SearchField, RowIDField


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
        """Create event and sync to FTS5 index."""
        raise NotImplementedError


class EventIndex(FTS5Model):
    """FTS5 full-text search index over events."""

    rowid = RowIDField()
    text = SearchField()
    event_type = SearchField(unindexed=True)

    class Meta:
        table_name = "event_index"
        options = {"tokenize": "porter unicode61"}
