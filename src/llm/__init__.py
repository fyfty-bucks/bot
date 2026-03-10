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
from src.llm.client import OpenRouterClient, load_api_key

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
        raise NotImplementedError

    def _resolve_model(self, tier: ModelTier) -> str:
        """Map tier enum to model slug from config."""
        raise NotImplementedError

    def close(self) -> None:
        """Release httpx client resources."""
        self._client.close()
