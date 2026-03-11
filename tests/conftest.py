"""Shared test fixtures."""

from collections.abc import Generator

import pytest
from playhouse.sqlite_ext import SqliteDatabase

from src.agent.db import get_db, create_tables, get_all_models


@pytest.fixture()
def test_db() -> Generator[SqliteDatabase, None, None]:
    """In-memory SQLite with all tables. Closes after test."""
    db = get_db(":memory:")
    create_tables(db, get_all_models())
    yield db
    if not db.is_closed():
        db.close()
