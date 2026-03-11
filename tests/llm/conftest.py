"""Shared fixtures for LLM tests."""

from collections.abc import Generator

import pytest
from playhouse.sqlite_ext import SqliteDatabase

from src.agent.config import Config
from src.agent.db import get_db, create_tables, get_all_models
from src.llm.client import RawResponse


@pytest.fixture()
def test_db() -> Generator[SqliteDatabase, None, None]:
    """In-memory SQLite with all tables including llm_cache."""
    db = get_db(":memory:")
    create_tables(db, get_all_models())
    yield db
    if not db.is_closed():
        db.close()


@pytest.fixture()
def test_config() -> Config:
    """Config with test defaults (cheap model, short cache TTL)."""
    return Config(
        model_fast="openai/gpt-4o-mini",
        model_smart="anthropic/claude-sonnet-4.5",
        budget_total=50.0,
        cache_ttl=3600,
        budget_alert_days=7,
    )


@pytest.fixture()
def sample_response() -> RawResponse:
    """Minimal valid RawResponse for test reuse."""
    return RawResponse(
        content="test response",
        model="openai/gpt-4o-mini",
        prompt_tokens=10,
        completion_tokens=5,
        cost=0.000005,
        finish_reason="stop",
        latency_ms=100,
    )
