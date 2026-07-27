"""Battery metrics utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def _get_battery_status_android(battery: dict[str, Any]) -> None:
    """Android fallback: /sys/class/power_supply/battery."""
    try:
        base = Path("/sys/class/power_supply/battery")
        if not base.is_dir():
            return

        def read_int(name: str) -> int | None:
            f = base / name
            if f.is_file():
                try:
                    return int(f.read_text().strip())
                except (OSError, ValueError) as exc:
                    logger.debug("Failed to read battery %s: %s", name, exc)
            return None

        capacity = read_int("capacity")
        status_file = base / "status"
        status = status_file.read_text().strip() if status_file.is_file() else ""
        plugged = status.lower() in ("charging", "full")
        battery["percent"] = capacity if capacity is not None else 0
        battery["power_plugged"] = plugged
        battery["secsleft"] = -1  # not easily available
    except OSError as exc:
        logger.debug("Battery fallback failed: %s", exc)


def get_battery_status() -> dict[str, Any]:
    """
    Return battery information (percent, power_plugged, time_left).

    Returns empty dict if no battery is present or info is unavailable.
    """
    battery: dict[str, Any] = {}
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            bat = psutil_helper.psutil.sensors_battery()
            if bat:
                battery["percent"] = bat.percent
                battery["power_plugged"] = bat.power_plugged
                battery["secsleft"] = bat.secsleft
        except OSError as exc:
            logger.debug("psutil sensors_battery failed: %s", exc)

    # Android fallback: /sys/class/power_supply/battery
    _get_battery_status_android(battery)

    return battery
