"""Client-side response cache backed by SQLite.

Stores LLM responses keyed by SHA256(model + messages + temperature).
Only caches deterministic calls (temperature == 0).
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone

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
        key = self.make_key(messages, model, temperature)
        now = datetime.now(timezone.utc)
        try:
            entry = CachedResponse.get(
                (CachedResponse.cache_key == key)
                & (CachedResponse.expires_at > now),
            )
        except CachedResponse.DoesNotExist:
            return None
        CachedResponse.update(
            hit_count=CachedResponse.hit_count + 1,
        ).where(CachedResponse.cache_key == key).execute()
        return RawResponse(**json.loads(entry.response_json))

    def put(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        response: RawResponse,
        ttl: int | None = None,
    ) -> None:
        """Store response in cache. ttl=None uses default."""
        if temperature != 0.0:
            return
        key = self.make_key(messages, model, temperature)
        effective_ttl = ttl if ttl is not None else self._default_ttl
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=effective_ttl)
        resp_json = json.dumps({
            "content": response.content,
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
            "finish_reason": response.finish_reason,
            "latency_ms": response.latency_ms,
        })
        db = CachedResponse._meta.database
        with db.atomic():
            CachedResponse.delete().where(
                CachedResponse.cache_key == key,
            ).execute()
            CachedResponse.create(
                cache_key=key,
                response_json=resp_json,
                model=model,
                created_at=now,
                expires_at=expires,
                hit_count=0,
            )

    @staticmethod
    def make_key(
        messages: list[dict], model: str, temperature: float,
    ) -> str:
        """SHA256 hash of canonical (model, messages, temperature)."""
        canonical = json.dumps(
            {"model": model, "messages": messages, "temperature": temperature},
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()
