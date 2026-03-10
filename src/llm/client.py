"""HTTP transport for OpenRouter API.

Handles request formatting, response parsing, retry logic.
Error types live in src/llm/errors.py.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

from src.llm.errors import ClientError, ServerError

logger = logging.getLogger("agent.llm.client")

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAYS = (1.0, 2.0, 4.0)


@dataclass(frozen=True)
class RawResponse:
    """Parsed completion response from OpenRouter."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    finish_reason: str
    latency_ms: int


def load_api_key() -> str:
    """Load API key: env var OPENROUTER_API_KEY > secrets/.openrouter_key."""
    raise NotImplementedError


class OpenRouterClient:
    """Thin httpx wrapper for OpenRouter chat completions."""

    def __init__(
        self, api_key: str, timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def send(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> RawResponse:
        """POST /chat/completions with retry on transient errors."""
        raise NotImplementedError

    def close(self) -> None:
        """Release httpx resources."""
        self._client.close()
