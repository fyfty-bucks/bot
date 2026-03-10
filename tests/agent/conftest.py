"""Shared fixtures for agent tests."""

from collections.abc import Generator

import pytest
from playhouse.sqlite_ext import SqliteDatabase

from src.agent.db import get_db, create_tables, ALL_MODELS


@pytest.fixture()
def test_db() -> Generator[SqliteDatabase, None, None]:
    """In-memory SQLite with pragmas. Creates all tables, closes after test."""
    db = get_db(":memory:")
    create_tables(db, ALL_MODELS)
    yield db
    if not db.is_closed():
        db.close()
