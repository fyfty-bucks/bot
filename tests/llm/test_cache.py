"""Tests for src/llm/cache.py — ResponseCache get/put, key generation."""

from datetime import datetime, timedelta, timezone

from src.llm.cache import CachedResponse, ResponseCache
from src.llm.client import RawResponse

MESSAGES = [{"role": "user", "content": "Hello"}]
MODEL = "openai/gpt-4o-mini"


def test_make_key_deterministic() -> None:
    """Same input produces same key."""
    k1 = ResponseCache.make_key(MESSAGES, MODEL, 0.0)
    k2 = ResponseCache.make_key(MESSAGES, MODEL, 0.0)
    assert k1 == k2
    assert len(k1) == 64


def test_make_key_differs_on_model() -> None:
    """Different model produces different key."""
    k1 = ResponseCache.make_key(MESSAGES, "model-a", 0.0)
    k2 = ResponseCache.make_key(MESSAGES, "model-b", 0.0)
    assert k1 != k2


def test_make_key_differs_on_temperature() -> None:
    """Different temperature produces different key."""
    k1 = ResponseCache.make_key(MESSAGES, MODEL, 0.0)
    k2 = ResponseCache.make_key(MESSAGES, MODEL, 0.7)
    assert k1 != k2


def test_make_key_differs_on_messages() -> None:
    """Different messages produce different key."""
    k1 = ResponseCache.make_key([{"role": "user", "content": "A"}], MODEL, 0.0)
    k2 = ResponseCache.make_key([{"role": "user", "content": "B"}], MODEL, 0.0)
    assert k1 != k2


def test_put_and_get(test_db, sample_response) -> None:
    """put() stores, get() retrieves identical RawResponse."""
    cache = ResponseCache(default_ttl=3600)
    cache.put(MESSAGES, MODEL, 0.0, sample_response)

    result = cache.get(MESSAGES, MODEL, 0.0)

    assert result is not None
    assert result.content == sample_response.content
    assert result.model == sample_response.model
    assert result.cost == sample_response.cost


def test_get_returns_none_on_miss(test_db) -> None:
    """get() returns None for uncached key."""
    cache = ResponseCache(default_ttl=3600)
    result = cache.get(MESSAGES, MODEL, 0.0)
    assert result is None


def test_get_returns_none_on_expired(test_db, sample_response) -> None:
    """get() returns None after TTL expiration."""
    cache = ResponseCache(default_ttl=3600)
    cache.put(MESSAGES, MODEL, 0.0, sample_response, ttl=1)

    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    CachedResponse.update(expires_at=past).where(
        CachedResponse.cache_key == ResponseCache.make_key(MESSAGES, MODEL, 0.0),
    ).execute()

    result = cache.get(MESSAGES, MODEL, 0.0)
    assert result is None


def test_get_increments_hit_count(test_db, sample_response) -> None:
    """get() increments hit_count on each hit."""
    cache = ResponseCache(default_ttl=3600)
    cache.put(MESSAGES, MODEL, 0.0, sample_response)

    cache.get(MESSAGES, MODEL, 0.0)
    cache.get(MESSAGES, MODEL, 0.0)
    cache.get(MESSAGES, MODEL, 0.0)

    key = ResponseCache.make_key(MESSAGES, MODEL, 0.0)
    entry = CachedResponse.get(CachedResponse.cache_key == key)
    assert entry.hit_count == 3


def test_put_overwrites_existing(test_db, sample_response) -> None:
    """put() with same key updates the stored response."""
    cache = ResponseCache(default_ttl=3600)
    cache.put(MESSAGES, MODEL, 0.0, sample_response)

    updated = RawResponse(
        content="updated",
        model=MODEL,
        prompt_tokens=20,
        completion_tokens=10,
        cost=0.00001,
        finish_reason="stop",
        latency_ms=200,
    )
    cache.put(MESSAGES, MODEL, 0.0, updated)

    result = cache.get(MESSAGES, MODEL, 0.0)
    assert result is not None
    assert result.content == "updated"
    assert CachedResponse.select().count() == 1


def test_put_skips_nonzero_temperature(test_db, sample_response) -> None:
    """put() does not cache when temperature != 0."""
    cache = ResponseCache(default_ttl=3600)
    cache.put(MESSAGES, MODEL, 0.7, sample_response)

    result = cache.get(MESSAGES, MODEL, 0.7)
    assert result is None
    assert CachedResponse.select().count() == 0
