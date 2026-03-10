"""Tests for database connection and infrastructure."""

from pathlib import Path

from src.agent.db import get_db, create_tables, get_all_models


def test_get_db_returns_connection() -> None:
    """get_db() returns an open database connection."""
    db = get_db(":memory:")
    assert not db.is_closed()
    db.close()


def test_wal_mode_enabled(tmp_path: Path) -> None:
    """WAL journal mode is set on file-based connection."""
    db_path = str(tmp_path / "test.db")
    db = get_db(db_path)
    cursor = db.execute_sql("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    assert mode == "wal"
    db.close()


def test_foreign_keys_enabled() -> None:
    """Foreign keys pragma is ON."""
    db = get_db(":memory:")
    cursor = db.execute_sql("PRAGMA foreign_keys")
    value = cursor.fetchone()[0]
    assert value == 1
    db.close()


def test_create_tables_idempotent() -> None:
    """Calling create_tables twice does not raise."""
    db = get_db(":memory:")
    create_tables(db, get_all_models())
    create_tables(db, get_all_models())
    db.close()


def test_migrate_adds_missing_tables() -> None:
    """All model tables exist after create_tables on empty DB."""
    db = get_db(":memory:")
    models = get_all_models()
    create_tables(db, models)
    tables = db.get_tables()
    assert len(tables) > 0
    for model in models:
        table_name = model._meta.table_name
        assert table_name in tables, f"Missing table: {table_name}"
    db.close()


def test_get_all_models_is_exported() -> None:
    """get_all_models is a public function, not a module-level constant."""
    from src.agent import db
    assert hasattr(db, "get_all_models"), "get_all_models must be exported"
    assert callable(db.get_all_models)
