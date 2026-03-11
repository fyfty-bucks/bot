"""LLM module — OpenRouter integration with caching and budget guard.

Public API: LLM class, LLMResult, ModelTier.
Orchestrates cache lookup, budget checking, HTTP transport, cost recording,
and alert emission on every call.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from playhouse.sqlite_ext import SqliteDatabase

from src.agent.config import Config
from src.llm.budget import BudgetExhausted, check_alerts, check_budget, record_cost
from src.llm.cache import ResponseCache
from src.llm.client import OpenRouterClient, RawResponse, load_api_key

logger = logging.getLogger("agent.llm")


class ModelTier(Enum):
    """Model selection tier. FAST = cheap default, SMART = expensive escalation."""

    FAST = "fast"
    SMART = "smart"


@dataclass(frozen=True)
class LLMResult:
    """Immutable outcome of an LLM call."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: int
    cached: bool
    finish_reason: str


class LLM:
    """Facade: cache → budget → client → record → alert → return."""

    def __init__(self, config: Config, db: SqliteDatabase) -> None:
        self._config = config
        self._db = db
        api_key = load_api_key()
        self._client = OpenRouterClient(api_key=api_key)
        self._cache = ResponseCache(default_ttl=config.cache_ttl)

    def call(
        self,
        messages: list[dict],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.0,
        max_tokens: int = 500,
        cache_ttl: int | None = None,
    ) -> LLMResult:
        """Send messages to LLM. Checks cache and budget, records cost."""
        from src.agent.models.events import Event

        cfg = self._config
        status = check_budget(cfg.budget_total, cfg.budget_alert_days)
        if status.level == "depleted":
            raise BudgetExhausted(status)
        if status.level in ("critical", "danger"):
            tier = ModelTier.FAST

        model = self._resolve_model(tier)
        skip_cache = cache_ttl == 0
        if not skip_cache:
            cached = self._cache.get(messages, model, temperature)
            if cached is not None:
                return self._build_result(cached, cached=True)

        raw = self._client.send(model, messages, max_tokens, temperature)
        record_cost(raw.cost, raw.model, raw.prompt_tokens + raw.completion_tokens)
        Event.log("llm_call", {
            "model": raw.model, "prompt_tokens": raw.prompt_tokens,
            "completion_tokens": raw.completion_tokens,
            "cost": raw.cost, "latency_ms": raw.latency_ms,
        })
        check_alerts(status)
        if not skip_cache:
            self._cache.put(messages, model, temperature, raw, ttl=cache_ttl)
        return self._build_result(raw, cached=False)

    @staticmethod
    def _build_result(raw: RawResponse, cached: bool) -> LLMResult:
        """Construct LLMResult from RawResponse."""
        return LLMResult(
            content=raw.content, model=raw.model,
            prompt_tokens=raw.prompt_tokens,
            completion_tokens=raw.completion_tokens,
            cost=raw.cost, latency_ms=raw.latency_ms,
            cached=cached, finish_reason=raw.finish_reason,
        )

    def _resolve_model(self, tier: ModelTier) -> str:
        """Map tier enum to model slug from config."""
        if tier == ModelTier.SMART:
            return self._config.model_smart
        return self._config.model_fast

    def close(self) -> None:
        """Release httpx client resources."""
        self._client.close()
