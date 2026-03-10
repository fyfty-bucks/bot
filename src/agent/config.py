"""Agent configuration — defaults + DB overrides + env overrides."""

import os
from dataclasses import dataclass, fields, field

from playhouse.sqlite_ext import SqliteDatabase


DEFAULTS = {
    "model_fast": "haiku",
    "model_smart": "sonnet",
    "budget_total": 50.0,
    "log_level": "INFO",
    "db_path": "agent.db",
}

ENV_PREFIX = "AGENT_"


@dataclass
class Config:
    """Typed config with 3-tier priority: env > db > defaults."""

    model_fast: str = field(default=DEFAULTS["model_fast"])
    model_smart: str = field(default=DEFAULTS["model_smart"])
    budget_total: float = field(default=DEFAULTS["budget_total"])
    log_level: str = field(default=DEFAULTS["log_level"])
    db_path: str = field(default=DEFAULTS["db_path"])

    @classmethod
    def load(cls, db: SqliteDatabase | None = None) -> "Config":
        """Load config: env > db > defaults. Type coercion with fallback."""
        raise NotImplementedError


def _load_from_db(db: SqliteDatabase) -> dict[str, str]:
    """Read all config entries from DB as a flat dict."""
    from src.agent.models.config_store import ConfigEntry

    result = {}
    try:
        for entry in ConfigEntry.select():
            result[entry.key] = entry.value
    except Exception:
        pass
    return result
