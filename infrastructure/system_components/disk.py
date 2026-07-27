"""Disk usage metrics utilities."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def get_disk_usage(path: str | Path = "/") -> dict[str, float]:
    """
    Return disk usage for *path* (total, used, free, percent).

    Args:
        path: Filesystem path (default root).

    Returns zeroes if unavailable.
    """
    disk = {"total": 0.0, "used": 0.0, "free": 0.0, "percent": 0.0}
    target = str(path)
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            usage = psutil_helper.psutil.disk_usage(target)
            disk.update(
                {
                    "total": float(usage.total),
                    "used": float(usage.used),
                    "free": float(usage.free),
                    "percent": usage.percent,
                }
            )
            return disk
        except OSError as exc:
            logger.debug("psutil disk_usage failed: %s", exc)
    # Fallback: use shutil.disk_usage (Python 3.3+)
    try:
        usage = shutil.disk_usage(target)
        used = float(usage.used)
        total = float(usage.total)
        percent = (used / total) * 100.0 if total > 0 else 0.0
        disk.update(
            {
                "total": total,
                "used": used,
                "free": float(usage.free),
                "percent": percent,
            }
        )
    except OSError as exc:
        logger.debug("shutil.disk_usage fallback failed: %s", exc)
    return disk
