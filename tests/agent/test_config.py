"""Tests for Config module — load() factory, defaults, DB overrides, env."""

import logging

import pytest

from src.agent.config import Config, DEFAULTS, _load_from_db
from src.agent.models.config_store import ConfigEntry


def test_config_load_defaults(test_db) -> None:
    """Config.load() returns default values when DB and env are empty."""
    cfg = Config.load(test_db)
    assert cfg.model_fast == "openai/gpt-4o-mini"
    assert cfg.model_smart == "anthropic/claude-sonnet-4.5"
    assert cfg.budget_total == 50.0
    assert cfg.cache_ttl == 604800
    assert cfg.budget_alert_days == 7


def test_config_load_no_db_uses_defaults() -> None:
    """Config.load() without DB returns pure defaults."""
    cfg = Config.load()
    assert cfg.model_fast == "openai/gpt-4o-mini"
    assert cfg.budget_total == 50.0
    assert cfg.db_path == "agent.db"


def test_config_from_db_overrides_default(test_db) -> None:
    """Value from DB overrides the default."""
    ConfigEntry.upsert("model_fast", "sonnet")
    cfg = Config.load(test_db)
    assert cfg.model_fast == "sonnet"


def test_config_from_env_overrides_db(
    test_db, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env variable overrides both DB and default."""
    ConfigEntry.upsert("model_fast", "sonnet")
    monkeypatch.setenv("AGENT_MODEL_FAST", "opus")
    cfg = Config.load(test_db)
    assert cfg.model_fast == "opus"


def test_config_unknown_key_ignored(test_db) -> None:
    """Unknown key in DB does not break config loading."""
    ConfigEntry.upsert("garbage_key_xyz", "whatever")
    cfg = Config.load(test_db)
    assert cfg.model_fast == "openai/gpt-4o-mini"


def test_config_invalid_db_value_falls_back(test_db) -> None:
    """Invalid DB value (e.g. non-numeric for float) falls back to default."""
    ConfigEntry.upsert("budget_total", "not_a_number")
    cfg = Config.load(test_db)
    assert cfg.budget_total == DEFAULTS["budget_total"]


def test_config_logs_warning_on_coercion_fallback(test_db, caplog) -> None:
    """Config.load() logs warning when type coercion fails for a key."""
    ConfigEntry.upsert("budget_total", "not_a_number")
    with caplog.at_level(logging.WARNING, logger="agent.config"):
        Config.load(test_db)
    assert any("budget_total" in r.message for r in caplog.records)


def test_load_from_db_logs_on_error(test_db, caplog) -> None:
    """_load_from_db logs a warning when DB query fails."""
    test_db.close()

    with caplog.at_level(logging.WARNING):
        result = _load_from_db(test_db)

    assert result == {}
    assert len(caplog.records) > 0
