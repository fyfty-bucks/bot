"""Tests for src/llm/__init__.py — LLM.call() integration."""

import json
from unittest.mock import patch, MagicMock

import httpx
import pytest

from src.agent.models.budget import BudgetLog
from src.agent.models.events import Event
from src.llm import LLM, LLMResult, ModelTier
from src.llm.budget import BudgetExhausted
from src.llm.client import RawResponse

MESSAGES = [{"role": "user", "content": "Hello"}]

API_RESPONSE = {
    "choices": [
        {
            "message": {"content": "Hi", "role": "assistant"},
            "finish_reason": "stop",
        }
    ],
    "model": "openai/gpt-4o-mini",
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "cost": 0.000005,
    },
}


def _make_llm(test_config, test_db) -> LLM:
    """Create LLM with mocked API key and transport."""
    with patch("src.llm.load_api_key", return_value="sk-test"):
        llm = LLM(config=test_config, db=test_db)
    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=API_RESPONSE),
    )
    llm._client._client = httpx.Client(transport=transport)
    return llm


def test_call_returns_llm_result(test_db, test_config) -> None:
    """call() returns LLMResult with all fields populated."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    result = llm.call(MESSAGES)

    assert isinstance(result, LLMResult)
    assert result.content == "Hi"
    assert result.model == "openai/gpt-4o-mini"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5
    assert result.cost == 0.000005
    assert result.cached is False
    assert result.finish_reason == "stop"
    llm.close()


def test_call_cache_hit(test_db, test_config) -> None:
    """Second identical call returns cached=True without API call."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    r1 = llm.call(MESSAGES, temperature=0.0)
    r2 = llm.call(MESSAGES, temperature=0.0)

    assert r1.cached is False
    assert r2.cached is True
    assert r2.content == r1.content
    llm.close()


def test_call_skips_cache_nonzero_temperature(test_db, test_config) -> None:
    """call(temperature=0.7) always hits API, never cache."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    r1 = llm.call(MESSAGES, temperature=0.7)
    r2 = llm.call(MESSAGES, temperature=0.7)

    assert r1.cached is False
    assert r2.cached is False
    llm.close()


def test_call_skips_cache_when_ttl_zero(test_db, test_config) -> None:
    """call(cache_ttl=0) bypasses cache."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    r1 = llm.call(MESSAGES, cache_ttl=0)
    r2 = llm.call(MESSAGES, cache_ttl=0)

    assert r1.cached is False
    assert r2.cached is False
    llm.close()


def test_call_records_cost(test_db, test_config) -> None:
    """call() creates BudgetLog entry with negative cost."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES)

    llm_entries = list(
        BudgetLog.select().where(BudgetLog.category == "llm"),
    )
    assert len(llm_entries) == 1
    assert llm_entries[0].amount < 0
    llm.close()


def test_call_logs_event(test_db, test_config) -> None:
    """call() creates Event(type='llm_call') with model/tokens/cost."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES)

    events = list(
        Event.select().where(Event.event_type == "llm_call"),
    )
    assert len(events) == 1
    payload = json.loads(events[0].payload)
    assert payload["model"] == "openai/gpt-4o-mini"
    assert "cost" in payload
    assert "prompt_tokens" in payload
    llm.close()


def test_call_raises_budget_exhausted(test_db, test_config) -> None:
    """call() raises BudgetExhausted when balance <= 0."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")
    BudgetLog.record(amount=-51.0, category="llm")

    with pytest.raises(BudgetExhausted):
        llm.call(MESSAGES)
    llm.close()


def test_call_forces_fast_on_critical(test_db, test_config) -> None:
    """call(tier=SMART) uses FAST model when budget is critical."""
    test_config_smart = test_config
    llm = _make_llm(test_config_smart, test_db)
    BudgetLog.record(amount=50.0, category="seed")
    BudgetLog.record(amount=-48.0, category="llm")

    result = llm.call(MESSAGES, tier=ModelTier.SMART)

    assert result.model == test_config.model_fast
    llm.close()


def test_resolve_model_fast(test_db, test_config) -> None:
    """_resolve_model(FAST) returns config.model_fast."""
    llm = _make_llm(test_config, test_db)
    assert llm._resolve_model(ModelTier.FAST) == "openai/gpt-4o-mini"
    llm.close()


def test_resolve_model_smart(test_db, test_config) -> None:
    """_resolve_model(SMART) returns config.model_smart."""
    llm = _make_llm(test_config, test_db)
    assert llm._resolve_model(ModelTier.SMART) == "openai/gpt-4o-mini"
    llm.close()
