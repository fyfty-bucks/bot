"""Event and FTS5 index models — stubs for TDD Phase 2."""

import peewee
from playhouse.sqlite_ext import FTS5Model, SearchField, RowIDField


class Event(peewee.Model):
    """Core event-sourced log. Stub — no fields yet."""

    class Meta:
        table_name = "events"

    def get_payload(self) -> dict:
        """Deserialize payload JSON."""
        raise NotImplementedError


class EventIndex(FTS5Model):
    """FTS5 full-text search index over events. Stub."""

    rowid = RowIDField()
    text = SearchField()
    event_type = SearchField(unindexed=True)

    class Meta:
        table_name = "event_index"
        options = {"tokenize": "porter unicode61"}
