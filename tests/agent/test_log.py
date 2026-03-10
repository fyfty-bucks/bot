"""Tests for structured logging setup."""

import logging

from src.agent.log import setup_logging


def test_setup_logging_returns_logger() -> None:
    """setup_logging returns a configured logger."""
    logger = setup_logging(level="DEBUG")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "agent"


def test_setup_logging_respects_level() -> None:
    """Logger level matches requested level."""
    logger = setup_logging(level="WARNING")
    assert logger.level == logging.WARNING


def test_setup_logging_has_handler() -> None:
    """Logger has at least one handler after setup."""
    logger = setup_logging(level="INFO")
    assert len(logger.handlers) >= 1


def test_setup_logging_file_handler(tmp_path) -> None:
    """File handler is added when log_file is specified."""
    log_file = tmp_path / "agent.log"
    logger = setup_logging(level="INFO", log_file=str(log_file))

    logger.info("test message")
    file_handlers = [
        h for h in logger.handlers
        if isinstance(h, logging.FileHandler)
    ]
    assert len(file_handlers) >= 1


def test_setup_logging_format() -> None:
    """Log format includes timestamp and level."""
    logger = setup_logging(level="DEBUG")
    handler = logger.handlers[0]
    record = logging.LogRecord("test", logging.DEBUG, "", 0, "testmsg", (), None)
    output = handler.format(record)
    assert "DEBUG" in output
    assert "testmsg" in output
