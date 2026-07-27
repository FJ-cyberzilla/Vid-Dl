"""Temperature metrics utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from infrastructure.system_components import psutil_helper

logger = logging.getLogger(__name__)


def _read_temp_file(path: Path) -> float:
    """Read and convert temperature from a sysfs file."""
    return float(path.read_text().strip()) / 1000.0


def _extract_temp_from_sensors(
    sensors: dict[str, Any], temps: dict[str, float]
) -> None:
    """Helper to extract temperatures from psutil sensors."""
    for name, entries in sensors.items():
        for entry in entries:
            label = entry.label or name
            temps[label] = entry.current


def _get_temperatures_via_psutil() -> dict[str, float]:
    """Gather temperatures using psutil."""
    temps: dict[str, float] = {}
    if psutil_helper._PSUTIL_AVAILABLE and psutil_helper.psutil:
        try:
            sensors = psutil_helper.psutil.sensors_temperatures()
            _extract_temp_from_sensors(sensors, temps)
        except OSError as exc:
            logger.debug("psutil sensors_temperatures failed: %s", exc)
    return temps


def _parse_thermal_zone_file(
    type_path: Path, temp_path: Path
) -> tuple[str, float] | None:
    """Read and parse type and temp files for a thermal zone."""
    try:
        type_name = type_path.read_text().strip()
        temp = _read_temp_file(temp_path)
        return type_name, temp
    except (OSError, ValueError) as exc:
        logger.debug("Could not read thermal zone paths: %s", exc)
        return None


def _process_thermal_zone(zone: Path) -> tuple[str, float] | None:
    """Read and parse a single thermal zone."""
    if not (zone.is_dir() and zone.name.startswith("thermal_zone")):
        return None
    type_path = zone / "type"
    temp_path = zone / "temp"
    if not (type_path.is_file() and temp_path.is_file()):
        return None
    return _parse_thermal_zone_file(type_path, temp_path)


def _get_temperatures_via_thermal_zones() -> dict[str, float]:
    """Gather temperatures from Linux thermal zones."""
    temps: dict[str, float] = {}
    try:
        base = Path("/sys/class/thermal")
        if not base.exists():
            return temps

        for zone in base.iterdir():
            result = _process_thermal_zone(zone)
            if result:
                temps[result[0]] = result[1]
    except OSError as exc:
        logger.debug("Thermal zone lookup failed: %s", exc)
    return temps


def get_temperatures() -> dict[str, float]:
    """
    Return a dict of sensor names and their temperatures in °C.

    On Linux/Android this may include ``cpu_thermal``, ``battery``, etc.
    Returns an empty dict if not available.
    """
    temps = _get_temperatures_via_psutil()
    if not temps:
        temps = _get_temperatures_via_thermal_zones()
    return temps
