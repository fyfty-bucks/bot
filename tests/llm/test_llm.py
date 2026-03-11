"""Tests for src/llm/__init__.py — LLM.call() integration."""

import json
from unittest.mock import patch

import httpx
import pytest

from src.agent.models.budget import BudgetLog
from src.agent.models.events import Event
from src.llm import LLM, LLMResult, ModelTier
from src.llm.budget import BudgetExhausted
from src.llm.cache import CachedResponse
from src.llm.client import RawResponse
from src.llm.errors import ClientError, ServerError

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
    """call() creates BudgetLog entry with exact API-reported cost."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES)

    llm_entries = list(
        BudgetLog.select().where(BudgetLog.category == "llm"),
    )
    assert len(llm_entries) == 1
    assert llm_entries[0].amount == -0.000005
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
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=API_RESPONSE)

    llm = _make_llm(test_config, test_db)
    llm._client._client = httpx.Client(transport=httpx.MockTransport(handler))
    BudgetLog.record(amount=50.0, category="seed")
    BudgetLog.record(amount=-39.0, category="llm")  # balance=11, ~2 days → critical

    llm.call(MESSAGES, tier=ModelTier.SMART)

    assert captured["body"]["model"] == test_config.model_fast
    llm.close()


def test_call_cache_hit_no_extra_cost(test_db, test_config) -> None:
    """Cache hit does not create additional BudgetLog entry."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES, temperature=0.0)
    llm.call(MESSAGES, temperature=0.0)

    llm_entries = list(
        BudgetLog.select().where(BudgetLog.category == "llm"),
    )
    assert len(llm_entries) == 1
    llm.close()


def test_call_smart_tier_sends_smart_model(test_db, test_config) -> None:
    """call(tier=SMART) sends model_smart when budget is OK."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=API_RESPONSE)

    llm = _make_llm(test_config, test_db)
    llm._client._client = httpx.Client(transport=httpx.MockTransport(handler))
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES, tier=ModelTier.SMART)

    assert captured["body"]["model"] == test_config.model_smart
    llm.close()


def test_resolve_model_fast(test_db, test_config) -> None:
    """_resolve_model(FAST) returns config.model_fast."""
    llm = _make_llm(test_config, test_db)
    assert llm._resolve_model(ModelTier.FAST) == test_config.model_fast
    llm.close()


def test_resolve_model_smart(test_db, test_config) -> None:
    """_resolve_model(SMART) returns config.model_smart."""
    llm = _make_llm(test_config, test_db)
    assert llm._resolve_model(ModelTier.SMART) == test_config.model_smart
    llm.close()


def test_call_propagates_client_error(test_db, test_config) -> None:
    """call() propagates ClientError from transport layer."""
    def failing_send(*args, **kwargs):
        raise ClientError(401, "unauthorized")

    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")
    llm._client.send = failing_send

    with pytest.raises(ClientError) as exc_info:
        llm.call(MESSAGES)
    assert exc_info.value.code == 401
    llm.close()


def test_call_propagates_server_error(test_db, test_config) -> None:
    """call() propagates ServerError from transport layer."""
    def failing_send(*args, **kwargs):
        raise ServerError(503, "unavailable")

    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")
    llm._client.send = failing_send

    with pytest.raises(ServerError) as exc_info:
        llm.call(MESSAGES)
    assert exc_info.value.code == 503
    llm.close()


def test_call_cache_ttl_zero_no_cache_row(test_db, test_config) -> None:
    """call(cache_ttl=0) does not write any row to llm_cache table."""
    llm = _make_llm(test_config, test_db)
    BudgetLog.record(amount=50.0, category="seed")

    llm.call(MESSAGES, cache_ttl=0)

    assert CachedResponse.select().count() == 0
    llm.close()
