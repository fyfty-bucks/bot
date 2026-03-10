"""Database connection, pragmas, and migration helpers."""

from playhouse.sqlite_ext import SqliteDatabase


def get_db(path: str = "agent.db") -> SqliteDatabase:
    """Create and return a configured SQLite connection."""
    raise NotImplementedError


def create_tables(db: SqliteDatabase, models: list) -> None:
    """Create all tables if they don't exist."""
    raise NotImplementedError


ALL_MODELS: list = []
