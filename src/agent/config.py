"""Agent configuration — defaults + DB overrides + env overrides."""

import logging
import os
from dataclasses import dataclass, fields, field

from playhouse.sqlite_ext import SqliteDatabase

logger = logging.getLogger("agent.config")

DEFAULTS = {
    "model_fast": "openai/gpt-4o-mini",
    "model_smart": "anthropic/claude-sonnet-4.5",
    "budget_total": 50.0,
    "log_level": "INFO",
    "db_path": "agent.db",
    "cache_ttl": 604800,
    "budget_alert_days": 7,
}

TYPE_MAP: dict[str, type] = {
    "model_fast": str,
    "model_smart": str,
    "budget_total": float,
    "log_level": str,
    "db_path": str,
    "cache_ttl": int,
    "budget_alert_days": int,
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
    cache_ttl: int = field(default=DEFAULTS["cache_ttl"])
    budget_alert_days: int = field(default=DEFAULTS["budget_alert_days"])

    @classmethod
    def load(cls, db: SqliteDatabase | None = None) -> "Config":
        """Load config: env > db > defaults. Type coercion with fallback."""
        db_values = _load_from_db(db) if db else {}
        kwargs: dict[str, object] = {}
        for f in fields(cls):
            default = DEFAULTS[f.name]
            raw = db_values.get(f.name)
            env_key = f"{ENV_PREFIX}{f.name.upper()}"
            env_val = os.environ.get(env_key)

            if env_val is not None:
                raw = env_val
            if raw is not None:
                try:
                    kwargs[f.name] = TYPE_MAP[f.name](raw)
                except (ValueError, TypeError):
                    logger.warning(
                        "Invalid config value for %s: %r, using default",
                        f.name, raw,
                    )
                    kwargs[f.name] = default
            else:
                kwargs[f.name] = default
        return cls(**kwargs)


def _load_from_db(db: SqliteDatabase) -> dict[str, object]:
    """Read all config entries from DB as a flat dict."""
    from src.agent.models.config_store import ConfigEntry

    result = {}
    try:
        for entry in ConfigEntry.select():
            result[entry.key] = entry.get_value()
    except Exception:
        logger.warning("Failed to load config from DB", exc_info=True)
    return result
