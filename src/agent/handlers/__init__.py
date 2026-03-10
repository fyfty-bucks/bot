"""Handler registry — stub for TDD Phase 2."""

from typing import Callable

HandlerFn = Callable[[dict], dict | None]


class HandlerRegistry:
    """Plugin registry for event handlers. Stub."""

    def __init__(self) -> None:
        self.handlers: dict[str, HandlerFn] = {}

    def register(self, name: str, handler: HandlerFn) -> None:
        """Register a handler for an event type."""
        raise NotImplementedError

    def route(self, event_type: str, event_data: dict) -> dict | None:
        """Route event to matching handler."""
        raise NotImplementedError

    def discover(self, package_path: str) -> None:
        """Auto-discover handler modules from a directory."""
        raise NotImplementedError
