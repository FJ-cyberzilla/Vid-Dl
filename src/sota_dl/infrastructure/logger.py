"""
Infrastructure - Structured Rotating Logger
Configures asynchronous and thread-safe rotating file logging while protecting the TUI.
"""

import logging
import structlog
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from sota_dl.infrastructure.app_dirs import LOG_DIR


@dataclass(slots=True, frozen=True)
class LoggerConfig:
    """Configuration settings for structured file logging."""

    log_file: Path = LOG_DIR / "app.log"
    max_bytes: int = 10 * 1024 * 1024  # 10 MB per log file
    backup_count: int = 5  # Retain up to 5 rotated files
    log_level: int = logging.INFO


def setup_logger(
    name: str = "app", config: LoggerConfig | None = None
) -> structlog.stdlib.BoundLogger:
    """
    Initializes and returns a structlog logger instance routed to a rotating file.
    """
    cfg = config or LoggerConfig()
    cfg.log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging to handle the file rotation
    handler = RotatingFileHandler(
        filename=cfg.log_file,
        maxBytes=cfg.max_bytes,
        backupCount=cfg.backup_count,
        encoding="utf-8",
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger = logging.getLogger(name)
    logger.setLevel(cfg.log_level)
    logger.propagate = False

    # Remove existing handlers to avoid duplication
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    logger.addHandler(handler)

    return structlog.get_logger(name)  # type: ignore[no-any-return]
