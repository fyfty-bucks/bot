"""HTTP transport for OpenRouter API.

Handles request formatting, response parsing, retry logic.
Error types live in src/llm/errors.py.
"""

import logging
import os
import time
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


def _parse_response(data: dict, latency: int) -> RawResponse:
    """Extract fields from OpenRouter response JSON."""
    if "choices" not in data or not data["choices"]:
        raise ClientError(502, "Malformed API response: missing 'choices'")
    choice = data["choices"][0]
    usage = data.get("usage", {})
    cost = usage.get("cost")
    if cost is None:
        logger.warning("API response missing usage.cost, defaulting to 0.0")
        cost = 0.0
    return RawResponse(
        content=choice["message"]["content"],
        model=data["model"],
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        cost=cost,
        finish_reason=choice.get("finish_reason", "unknown"),
        latency_ms=latency,
    )


def load_api_key() -> str:
    """Load API key: env var OPENROUTER_API_KEY > secrets/.openrouter_key."""
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key
    key_path = Path("secrets/.openrouter_key")
    if key_path.exists():
        return key_path.read_text().strip()
    raise RuntimeError("API key not found: set OPENROUTER_API_KEY or create secrets/.openrouter_key")


def _extract_error_msg(resp: httpx.Response) -> str:
    """Pull error message from JSON body, fall back to raw text."""
    try:
        return resp.json().get("error", {}).get("message", resp.text)
    except Exception:
        return resp.text


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
        payload = {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature,
            "user": "50bucks-agent",
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        last_exc: ServerError | None = None
        retries_408 = 1

        for attempt in range(MAX_RETRIES + 1):
            t0 = int(time.monotonic() * 1000)
            try:
                resp = self._client.post(
                    f"{BASE_URL}/chat/completions", json=payload, headers=headers,
                )
            except httpx.TimeoutException as exc:
                last_exc = ServerError(408, str(exc))
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])
                    continue
                raise last_exc from exc
            latency = int(time.monotonic() * 1000) - t0
            code = resp.status_code
            if code == 200:
                return _parse_response(resp.json(), latency)
            msg = _extract_error_msg(resp)
            if code in (400, 401, 402, 403):
                raise ClientError(code, msg)
            if code == 408 and retries_408 > 0 and attempt < MAX_RETRIES:
                retries_408 -= 1
                time.sleep(RETRY_DELAYS[0])
                continue
            if code == 408:
                raise ServerError(code, msg)
            if code in (429, 502, 503):
                last_exc = ServerError(code, msg)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)])
                    continue
                raise last_exc
            raise ClientError(code, msg)
        raise AssertionError("unreachable: retry loop exited without return or raise")

    def close(self) -> None:
        """Release httpx resources."""
        self._client.close()
