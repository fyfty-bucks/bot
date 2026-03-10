"""Agent core loop — receive, route, execute, store."""

import json
import logging
from dataclasses import dataclass

from playhouse.sqlite_ext import SqliteDatabase

from src.agent.handlers import HandlerRegistry
from src.agent.models.events import Event

logger = logging.getLogger("agent")


@dataclass
class HandleResult:
    """Outcome of execute(): distinguishes unhandled, success, and error."""

    handled: bool
    result: dict | None = None
    error: str | None = None


class AgentCore:
    """Event-triggered agent. Receives events, routes to handlers, stores results."""

    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db
        self.registry = HandlerRegistry()

    def receive(self, event_type: str, data: dict) -> Event:
        """Store an incoming event with FTS5 sync."""
        event = Event.log(event_type, data)
        logger.debug("Received event %s id=%d", event_type, event.id)
        return event

    def execute(self, event: Event) -> HandleResult:
        """Route event to handler. Returns HandleResult with clear outcome."""
        data = json.loads(event.payload)
        handler = self.registry.handlers.get(event.event_type)

        if handler is None:
            return HandleResult(handled=False)

        try:
            result = handler(data)
        except Exception as exc:
            logger.error("Handler error for %s: %s", event.event_type, exc)
            self._store_event("error", {
                "source_event_id": event.id,
                "source_event_type": event.event_type,
                "error": str(exc),
            })
            return HandleResult(handled=True, error=str(exc))

        if result is not None:
            self._store_event("handler_result", result)

        return HandleResult(handled=True, result=result)

    def _store_event(self, event_type: str, data: dict) -> None:
        """Best-effort event storage. Logs failure instead of crashing."""
        try:
            Event.log(event_type, data)
        except Exception as exc:
            logger.error("Failed to store %s event: %s", event_type, exc)
