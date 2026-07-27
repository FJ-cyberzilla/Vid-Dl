"""CPU metrics utilities."""

from __future__ import annotations

import logging
import os
from typing import Any

from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def get_cpu_usage(interval: float = 1.0) -> float:
    """
    Return overall CPU usage percent (0‑100).

    Args:
        interval: Seconds to measure over. Ignored if psutil unavailable.

    Returns:
        CPU utilisation as a float, or -1.0 if not measurable.
    """
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            return float(psutil_helper.psutil.cpu_percent(interval=interval))
        except OSError as exc:
            logger.debug("psutil cpu_percent failed: %s", exc)
    return -1.0


def get_per_cpu_usage(interval: float = 1.0) -> list[float]:
    """
    Return per‑core CPU usage as a list of floats (0‑100).

    Returns an empty list if psutil is unavailable.
    """
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            return list(
                psutil_helper.psutil.cpu_percent(interval=interval, percpu=True)
            )
        except OSError as exc:
            logger.debug("psutil cpu_percent percpu failed: %s", exc)
    return []


def _get_psutil_cpu_count(logical: bool = True) -> int | None:
    """Get CPU count via psutil."""
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            count = psutil_helper.psutil.cpu_count(logical=logical)
            return int(count) if count is not None else None
        except OSError as exc:
            logger.debug("psutil cpu_count failed: %s", exc)
    return None


def get_cpu_count() -> int:
    """Return the number of logical CPUs."""
    count = _get_psutil_cpu_count(logical=True)
    if count is not None:
        return int(count or 1)

    # Fallback: try os.cpu_count()
    try:
        return os.cpu_count() or 1
    except OSError:
        return 1


def get_physical_cpu_count() -> int:
    """Return the number of physical CPU cores."""
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            return int(psutil_helper.psutil.cpu_count(logical=False) or 1)
        except OSError as exc:
            logger.debug("psutil cpu_count physical failed: %s", exc)
    # Fallback: use logical count
    return get_cpu_count()


def get_cpu_frequency() -> dict[str, Any]:
    """
    Return current CPU frequency info.

    Returns a dict with keys ``current``, ``min``, ``max`` (MHz) or empty.
    """
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            freq = psutil_helper.psutil.cpu_freq()
            if freq:
                return {
                    "current": float(freq.current),
                    "min": float(freq.min),
                    "max": float(freq.max),
                }
        except OSError as exc:
            logger.debug("psutil cpu_freq failed: %s", exc)
    return {}


def _get_load_avg_fallback() -> tuple[float, float, float]:
    """Read /proc/loadavg manually."""
    try:
        with open("/proc/loadavg", encoding="utf-8") as f:
            parts = f.read().strip().split()
            if len(parts) >= 3:
                return (float(parts[0]), float(parts[1]), float(parts[2]))
    except OSError as exc:
        logger.debug("/proc/loadavg read failed: %s", exc)
    return (0.0, 0.0, 0.0)


def get_load_average() -> tuple[float, float, float]:
    """Return the 1, 5, 15 minute load averages (Linux/Android)."""
    if (
        psutil_helper._PSUTIL_AVAILABLE
        and psutil_helper.psutil
        and hasattr(psutil_helper.psutil, "getloadavg")
    ):
        try:
            avg = psutil_helper.psutil.getloadavg()
            return (float(avg[0]), float(avg[1]), float(avg[2]))
        except (OSError, AttributeError, IndexError) as exc:
            logger.debug("psutil getloadavg failed: %s", exc)
    # Fallback: read /proc/loadavg manually
    return _get_load_avg_fallback()
