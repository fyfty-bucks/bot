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

    def __init__(self, db: SqliteDatabase | None = None) -> None:
        db_values = _load_from_db(db) if db else {}
        for f in fields(self.__class__):
            default = DEFAULTS.get(f.name, f.default)
            from_db = db_values.get(f.name)
            from_env = os.environ.get(f"{ENV_PREFIX}{f.name.upper()}")

            raw = from_env if from_env is not None else (
                from_db if from_db is not None else default
            )
            setattr(self, f.name, f.type(raw))


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
