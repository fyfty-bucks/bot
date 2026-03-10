"""Tests for Config module — defaults, DB overrides, env overrides."""

import os

import pytest

from src.agent.config import Config
from src.agent.models.config_store import ConfigEntry


def test_config_defaults(test_db) -> None:
    """Config returns default values when DB and env are empty."""
    cfg = Config(test_db)
    assert cfg.model_fast == "haiku"
    assert cfg.model_smart == "sonnet"
    assert cfg.budget_total == 50.0


def test_config_from_db_overrides_default(test_db) -> None:
    """Value from DB overrides the default."""
    ConfigEntry.upsert("model_fast", "sonnet")
    cfg = Config(test_db)
    assert cfg.model_fast == "sonnet"


def test_config_from_env_overrides_db(test_db, monkeypatch: pytest.MonkeyPatch) -> None:
    """Env variable overrides both DB and default."""
    ConfigEntry.upsert("model_fast", "sonnet")
    monkeypatch.setenv("AGENT_MODEL_FAST", "opus")
    cfg = Config(test_db)
    assert cfg.model_fast == "opus"


def test_config_priority_order(test_db, monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority: env > db > defaults."""
    ConfigEntry.upsert("budget_total", "30.0")
    monkeypatch.setenv("AGENT_BUDGET_TOTAL", "10.0")
    cfg = Config(test_db)
    assert cfg.budget_total == 10.0


def test_config_unknown_key_ignored(test_db) -> None:
    """Unknown key in DB does not break config loading."""
    ConfigEntry.upsert("garbage_key_xyz", "whatever")
    cfg = Config(test_db)
    assert cfg.model_fast == "haiku"
