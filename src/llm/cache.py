"""Client-side response cache backed by SQLite.

Stores LLM responses keyed by SHA256(model + messages + temperature).
Only caches deterministic calls (temperature == 0).
"""

import hashlib
import json
from datetime import datetime, timezone

import peewee

from src.llm.client import RawResponse


class CachedResponse(peewee.Model):
    """Persisted LLM response for cache hits."""

    cache_key = peewee.CharField(max_length=64, unique=True, index=True)
    response_json = peewee.TextField()
    model = peewee.CharField(max_length=100)
    created_at = peewee.DateTimeField(
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at = peewee.DateTimeField()
    hit_count = peewee.IntegerField(default=0)

    class Meta:
        table_name = "llm_cache"


class ResponseCache:
    """Get/put interface over CachedResponse table."""

    def __init__(self, default_ttl: int = 604800) -> None:
        self._default_ttl = default_ttl

    def get(
        self, messages: list[dict], model: str, temperature: float,
    ) -> RawResponse | None:
        """Return cached response if exists and not expired, else None."""
        raise NotImplementedError

    def put(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        response: RawResponse,
        ttl: int | None = None,
    ) -> None:
        """Store response in cache. ttl=None uses default."""
        raise NotImplementedError

    @staticmethod
    def make_key(
        messages: list[dict], model: str, temperature: float,
    ) -> str:
        """SHA256 hash of canonical (model, messages, temperature)."""
        raise NotImplementedError
