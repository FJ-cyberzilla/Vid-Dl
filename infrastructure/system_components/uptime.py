"""Uptime metrics utilities."""

from __future__ import annotations

import logging
import time
from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def get_uptime_seconds() -> float:
    """Return system uptime in seconds, or 0.0 if unknown."""
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            return float(time.time() - psutil_helper.psutil.boot_time())
        except OSError as exc:
            logger.debug("psutil boot_time failed: %s", exc)
    # Read /proc/uptime (Linux/Android)
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            return float(f.readline().split()[0])
    except (OSError, ValueError) as exc:
        logger.debug("/proc/uptime read failed: %s", exc)
    return 0.0
