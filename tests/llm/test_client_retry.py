"""Tests for src/llm/client.py — retry logic and edge cases."""

import json
from unittest.mock import patch

import httpx
import pytest

from src.llm.client import OpenRouterClient, RawResponse
from src.llm.errors import ClientError, ServerError

MESSAGES = [{"role": "user", "content": "Say OK"}]
MODEL = "openai/gpt-4o-mini"

API_RESPONSE_OK = {
    "choices": [
        {
            "message": {"content": "OK", "role": "assistant"},
            "finish_reason": "stop",
        }
    ],
    "model": MODEL,
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 2,
        "total_tokens": 12,
        "cost": 0.000003,
    },
}


@patch("src.llm.client.time.sleep")
def test_send_timeout_408_retries_once(_sleep) -> None:
    """send() retries once on HTTP 408, then succeeds."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(
                408, json={"error": {"message": "timeout", "code": 408}},
            )
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert result.content == "OK"
    assert call_count == 2
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_persistent_408_raises_server_error(_sleep) -> None:
    """send() raises ServerError after both 408 retries fail."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            408, json={"error": {"message": "timeout", "code": 408}},
        )

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ServerError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 408
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_httpx_timeout_retries_then_raises(_sleep) -> None:
    """send() retries on httpx.TimeoutException, raises ServerError when exhausted."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        raise httpx.TimeoutException("connection timed out")

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ServerError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 408
    assert call_count == 4  # 1 initial + 3 retries
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_httpx_timeout_recovers_on_retry(_sleep) -> None:
    """send() retries on timeout and succeeds if next attempt works."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.TimeoutException("connection timed out")
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert result.content == "OK"
    assert call_count == 2
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_408_on_last_attempt_raises(_sleep) -> None:
    """send() raises ServerError when 408 arrives on final attempt (not AssertionError)."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count <= 3:
            return httpx.Response(
                502, json={"error": {"message": "bad gateway", "code": 502}},
            )
        return httpx.Response(
            408, json={"error": {"message": "timeout", "code": 408}},
        )

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ServerError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 408
    assert call_count == 4
    client.close()


def test_send_malformed_response_no_choices() -> None:
    """send() raises ClientError when API response lacks 'choices' key."""
    body = {"model": MODEL, "usage": {"prompt_tokens": 0, "completion_tokens": 0}}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ClientError):
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    client.close()
