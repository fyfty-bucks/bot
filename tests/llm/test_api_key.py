"""Tests for load_api_key() — API key resolution from env and file."""

import pytest

from src.llm.client import load_api_key


def test_load_api_key_from_env(monkeypatch) -> None:
    """load_api_key() returns OPENROUTER_API_KEY env var."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-123")
    assert load_api_key() == "sk-test-123"


def test_load_api_key_from_file(tmp_path, monkeypatch) -> None:
    """load_api_key() falls back to secrets/.openrouter_key file."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    key_file = tmp_path / ".openrouter_key"
    key_file.write_text("sk-file-key\n")
    monkeypatch.setattr(
        "src.llm.client.Path",
        lambda *_: tmp_path / ".openrouter_key",
    )
    result = load_api_key()
    assert result == "sk-file-key"


def test_load_api_key_missing_raises(monkeypatch, tmp_path) -> None:
    """load_api_key() raises when no key source available."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    missing = tmp_path / "nonexistent"
    monkeypatch.setattr(
        "src.llm.client.Path",
        lambda *_: missing,
    )
    with pytest.raises(RuntimeError, match="API key"):
        load_api_key()
