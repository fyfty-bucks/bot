"""Database connection, pragmas, and migration helpers."""

from playhouse.sqlite_ext import SqliteDatabase


def get_db(path: str = "agent.db") -> SqliteDatabase:
    """Create and return a configured SQLite connection.

    Caller is responsible for closing via db.close().
    """
    db = SqliteDatabase(
        path,
        pragmas={
            "journal_mode": "wal",
            "foreign_keys": 1,
            "cache_size": -8000,
            "busy_timeout": 5000,
        },
    )
    db.connect(reuse_if_open=True)
    return db


def create_tables(db: SqliteDatabase, models: list) -> None:
    """Create all tables if they don't exist. Safe to call repeatedly."""
    db.bind(models)
    db.create_tables(models, safe=True)


def get_all_models() -> list:
    """Import and return all model classes. Lazy to avoid circular imports."""
    from src.agent.models import (
        Event, EventIndex, BudgetLog, Task, ConfigEntry,
    )
    return [Event, EventIndex, BudgetLog, Task, ConfigEntry]
