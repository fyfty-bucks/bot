"""LLM error types — API error classification for retry logic."""


class ClientError(Exception):
    """Non-retryable API error (400, 401, 402, 403)."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"HTTP {code}: {message}")


class ServerError(Exception):
    """Retryable API error (429, 502, 503)."""

    def __init__(
        self, code: int, message: str, retry_after: float | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"HTTP {code}: {message}")
