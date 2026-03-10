"""Handler registry — discover, register, route event handlers."""

import importlib
import importlib.util
import logging
import pkgutil
from pathlib import Path
from typing import Callable

HandlerFn = Callable[[dict], dict | None]
logger = logging.getLogger("agent.handlers")


class HandlerRegistry:
    """Plugin registry for event handlers."""

    def __init__(self) -> None:
        self.handlers: dict[str, HandlerFn] = {}

    def register(self, name: str, handler: HandlerFn) -> None:
        """Register a handler function for the given event type name."""
        self.handlers[name] = handler

    def route(self, event_type: str, event_data: dict) -> dict | None:
        """Route event to matching handler. Returns None if no match."""
        handler = self.handlers.get(event_type)
        if handler is None:
            return None
        return handler(event_data)

    def discover(self, package_path: str) -> None:
        """Auto-discover handler modules from a directory.

        Each module must export `name` (str) and `handle` (callable).
        """
        path = Path(package_path)
        for info in pkgutil.iter_modules([str(path)]):
            if info.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    info.name, str(path / f"{info.name}.py"),
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "name") and hasattr(mod, "handle"):
                        self.register(mod.name, mod.handle)
            except Exception as exc:
                logger.warning("Failed to load handler %s: %s", info.name, exc)
