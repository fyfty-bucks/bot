"""Agent core loop — stub for TDD Phase 2."""

from playhouse.sqlite_ext import SqliteDatabase

from src.agent.models.events import Event


class AgentCore:
    """Event-triggered agent. Stub — no implementation yet."""

    def __init__(self, db: SqliteDatabase) -> None:
        from src.agent.handlers import HandlerRegistry
        self.db = db
        self.registry = HandlerRegistry()

    def receive(self, event_type: str, data: dict) -> Event:
        """Store an incoming event."""
        raise NotImplementedError

    def execute(self, event: Event) -> dict | None:
        """Route event to handler, store result or error."""
        raise NotImplementedError
