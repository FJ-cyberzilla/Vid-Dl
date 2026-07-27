"""Memory and Swap metrics utilities."""

from __future__ import annotations

import logging
from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def _parse_meminfo_line(line: str, results: dict[str, int]) -> None:
    """Helper to parse a single line from /proc/meminfo."""
    parts = line.split()
    if not parts:
        return
    key = parts[0].replace(":", "")
    if key in results:
        results[key] = int(parts[1]) * 1024  # kB to bytes


def _parse_meminfo(keys: list[str]) -> dict[str, int]:
    """Parse /proc/meminfo for specified keys."""
    results = {key: 0 for key in keys}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                _parse_meminfo_line(line, results)
    except OSError as exc:
        logger.debug("/proc/meminfo read failed: %s", exc)
    return results


def get_memory_usage() -> dict[str, float]:
    """
    Return a dict with ``total``, ``available``, ``percent``, ``used`` bytes.

    Returns zeroes if information cannot be obtained.
    """
    mem_info = {
        "total": 0.0,
        "available": 0.0,
        "percent": 0.0,
        "used": 0.0,
    }
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            mem = psutil_helper.psutil.virtual_memory()
            mem_info.update(
                {
                    "total": float(mem.total),
                    "available": float(mem.available),
                    "percent": mem.percent,
                    "used": float(mem.used),
                }
            )
            return mem_info
        except OSError as exc:
            logger.debug("psutil virtual_memory failed: %s", exc)
    # Fallback via /proc/meminfo (Linux/Android)
    mem_data = _parse_meminfo(["MemTotal", "MemAvailable"])
    mem_total = mem_data["MemTotal"]
    mem_avail = mem_data["MemAvailable"]
    if mem_total > 0:
        used = mem_total - mem_avail
        percent = (used / mem_total) * 100.0
        mem_info.update(
            {
                "total": float(mem_total),
                "available": float(mem_avail),
                "percent": percent,
                "used": float(used),
            }
        )
        return mem_info
    return mem_info


def get_swap_usage() -> dict[str, float]:
    """Return swap memory info (total, used, percent) or zeroes."""
    swap_info = {"total": 0.0, "used": 0.0, "percent": 0.0}
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            swap = psutil_helper.psutil.swap_memory()
            swap_info.update(
                {
                    "total": float(swap.total),
                    "used": float(swap.used),
                    "percent": swap.percent,
                }
            )
            return swap_info
        except OSError as exc:
            logger.debug("psutil swap_memory failed: %s", exc)
    # Fallback via /proc/meminfo
    swap_data = _parse_meminfo(["SwapTotal", "SwapFree"])
    total = swap_data["SwapTotal"]
    free = swap_data["SwapFree"]
    if total > 0:
        used = total - free
        percent = (used / total) * 100.0
        swap_info.update(
            {
                "total": float(total),
                "used": float(used),
                "percent": percent,
            }
        )
    return swap_info
