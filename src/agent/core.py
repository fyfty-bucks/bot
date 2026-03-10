"""Agent core loop — receive, route, execute, store."""

import json
import logging

from playhouse.sqlite_ext import SqliteDatabase

from src.agent.handlers import HandlerRegistry
from src.agent.models.events import Event

logger = logging.getLogger("agent")


class AgentCore:
    """Event-triggered agent. Receives events, routes to handlers, stores results."""

    def __init__(self, db: SqliteDatabase) -> None:
        self.db = db
        self.registry = HandlerRegistry()

    def receive(self, event_type: str, data: dict) -> Event:
        """Store an incoming event and return the Event record."""
        event = Event.create(
            event_type=event_type,
            payload=json.dumps(data),
        )
        logger.debug("Received event %s id=%d", event_type, event.id)
        return event

    def execute(self, event: Event) -> dict | None:
        """Route event to handler, store result or error."""
        data = json.loads(event.payload)
        try:
            result = self.registry.route(event.event_type, data)
        except Exception as exc:
            logger.error("Handler error for %s: %s", event.event_type, exc)
            Event.create(
                event_type="error",
                payload=json.dumps({
                    "source_event_id": event.id,
                    "source_event_type": event.event_type,
                    "error": str(exc),
                }),
            )
            return None

        if result is not None:
            Event.create(
                event_type="handler_result",
                payload=json.dumps(result),
            )

        return result
