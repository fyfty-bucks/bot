"""Shared fixtures for LLM tests."""

import pytest

from src.agent.config import Config
from src.llm.client import RawResponse


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
