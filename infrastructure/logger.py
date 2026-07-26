"""
Infrastructure - Structured Rotating Logger
Configures asynchronous and thread-safe rotating file logging while protecting the TUI.
"""

import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from infrastructure.app_dirs import LOG_DIR


@dataclass(slots=True, frozen=True)
class LoggerConfig:
    """Configuration settings for structured file logging."""

    log_file: Path = LOG_DIR / "app.log"
    max_bytes: int = 10 * 1024 * 1024  # 10 MB per log file
    backup_count: int = 5  # Retain up to 5 rotated files
    log_level: int = logging.INFO
    log_format: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "app", config: LoggerConfig | None = None
) -> logging.Logger:
    """
    Initializes and returns a logger instance routed strictly to a rotating file.

    :param name: Module name or namespace for the logger instance.
    :param config: LoggerConfig instance with custom file size or log level options.
    """
    cfg = config or LoggerConfig()

    # Ensure target directory exists
    cfg.log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(cfg.log_level)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        return logger

    # Prevent logs from propagating to root logger (which might pollute stdout/stderr)
    logger.propagate = False

    # Rotating File Handler
    file_handler = RotatingFileHandler(
        filename=cfg.log_file,
        maxBytes=cfg.max_bytes,
        backupCount=cfg.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(cfg.log_level)

    formatter = logging.Formatter(fmt=cfg.log_format, datefmt=cfg.date_format)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger
