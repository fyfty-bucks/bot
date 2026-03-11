"""Tests for src/llm/client.py — OpenRouterClient, load_api_key."""

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


def _mock_transport(status: int, body: dict) -> httpx.MockTransport:
    """Create httpx transport returning fixed status + JSON body."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body)
    return httpx.MockTransport(handler)


def test_send_success() -> None:
    """send() returns RawResponse on 200."""
    transport = _mock_transport(200, API_RESPONSE_OK)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)

    assert isinstance(result, RawResponse)
    assert result.content == "OK"
    assert result.model == MODEL
    client.close()


def test_send_parses_usage_fields() -> None:
    """send() extracts prompt_tokens, completion_tokens, cost from usage."""
    transport = _mock_transport(200, API_RESPONSE_OK)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)

    assert result.prompt_tokens == 10
    assert result.completion_tokens == 2
    assert result.cost == 0.000003
    assert result.finish_reason == "stop"
    assert result.latency_ms >= 0
    client.close()


def test_send_client_error_400() -> None:
    """send() raises ClientError on HTTP 400."""
    body = {"error": {"message": "bad request", "code": 400}}
    transport = _mock_transport(400, body)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ClientError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 400
    client.close()


def test_send_client_error_401() -> None:
    """send() raises ClientError on HTTP 401."""
    body = {"error": {"message": "unauthorized", "code": 401}}
    transport = _mock_transport(401, body)
    client = OpenRouterClient(api_key="sk-bad", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ClientError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 401
    client.close()


def test_send_client_error_402() -> None:
    """send() raises ClientError(402) on insufficient credits."""
    body = {"error": {"message": "insufficient credits", "code": 402}}
    transport = _mock_transport(402, body)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ClientError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 402
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_server_error_429_retries(_sleep) -> None:
    """send() retries on HTTP 429 with backoff, then succeeds."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(
                429,
                json={"error": {"message": "rate limited", "code": 429}},
            )
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert result.content == "OK"
    assert call_count == 3
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_server_error_502_retries(_sleep) -> None:
    """send() retries on HTTP 502, then succeeds."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(
                502, json={"error": {"message": "bad gateway", "code": 502}},
            )
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert call_count == 2
    assert result.content == "OK"
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_retries_exhaust_raises(_sleep) -> None:
    """send() raises ServerError after MAX_RETRIES failed attempts."""
    transport = _mock_transport(
        503, {"error": {"message": "unavailable", "code": 503}},
    )
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ServerError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 503
    client.close()


def test_send_includes_user_field() -> None:
    """send() includes user field for sticky routing."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)

    assert "user" in captured["body"]
    client.close()


def test_close() -> None:
    """close() releases httpx client without error."""
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client.close()


def test_send_client_error_403() -> None:
    """send() raises ClientError on HTTP 403."""
    body = {"error": {"message": "forbidden", "code": 403}}
    transport = _mock_transport(403, body)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ClientError) as exc_info:
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    assert exc_info.value.code == 403
    client.close()


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


def test_send_includes_auth_header() -> None:
    """send() sends Authorization: Bearer header."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test-key", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)

    assert captured["headers"]["authorization"] == "Bearer sk-test-key"
    client.close()


def test_send_forwards_max_tokens() -> None:
    """send() includes max_tokens in request body."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=API_RESPONSE_OK)

    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    client.send(MODEL, MESSAGES, max_tokens=42, temperature=0)

    assert captured["body"]["max_tokens"] == 42
    client.close()


@patch("src.llm.client.time.sleep")
def test_send_persistent_408_raises_server_error(_sleep) -> None:
    """send() raises ServerError after both 408 retries fail."""
    transport = _mock_transport(
        408, {"error": {"message": "timeout", "code": 408}},
    )
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

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
    transport = _mock_transport(200, body)
    client = OpenRouterClient(api_key="sk-test", timeout=5.0)
    client._client = httpx.Client(transport=transport)

    with pytest.raises(ClientError):
        client.send(MODEL, MESSAGES, max_tokens=10, temperature=0)
    client.close()
