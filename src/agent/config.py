"""Agent configuration — stub for TDD Phase 2."""

from dataclasses import dataclass

from playhouse.sqlite_ext import SqliteDatabase


@dataclass
class Config:
    """Typed config. Stub — no implementation yet."""

    model_fast: str = "haiku"
    model_smart: str = "sonnet"
    budget_total: float = 50.0
    log_level: str = "INFO"
    db_path: str = "agent.db"

    def __init__(self, db: SqliteDatabase | None = None) -> None:
        raise NotImplementedError
