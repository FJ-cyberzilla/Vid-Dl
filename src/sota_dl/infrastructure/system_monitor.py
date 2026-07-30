"""System metrics and environment monitoring utilities."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any

# psutil helper
try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    _PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# --- Environment Detection (formerly env.py) ---


def is_linux() -> bool:
    """Return ``True`` if running on Linux (including Android)."""
    return platform.system().lower() == "linux"


def is_android() -> bool:
    """Return ``True`` if running on Android."""
    if not is_linux():
        return False
    if is_termux():
        return True
    if os.environ.get("ANDROID_ROOT"):
        return True
    return Path("/system/build.prop").exists()


def is_termux() -> bool:
    """Return ``True`` if running inside Termux."""
    return os.environ.get("TERMUX_VERSION") is not None


def get_environment_name() -> str:
    """Return a human‑readable environment name."""
    if is_termux():
        return "Termux (Android)"
    if is_android():
        return "Android"
    system = platform.system()
    if system == "Linux":
        return "Linux"
    return system


def get_os() -> str:
    """Return the operating system name."""
    return platform.system()


def get_os_version() -> str:
    """Return OS version string."""
    return platform.version()


def get_architecture() -> str:
    """Return machine architecture (e.g. 'x86_64', 'aarch64')."""
    return platform.machine()


def get_python_version() -> str:
    """Return the Python version string."""
    return platform.python_version()


def get_hostname() -> str:
    """Return the system hostname."""
    return platform.node()


# --- CPU Metrics (formerly cpu.py) ---


def get_cpu_usage(interval: float = 1.0) -> float:
    """Return overall CPU usage percent (0‑100)."""
    if _PSUTIL_AVAILABLE and psutil:
        try:
            return float(psutil.cpu_percent(interval=interval))
        except OSError as exc:
            logger.debug("psutil cpu_percent failed: %s", exc)
    return -1.0


def get_per_cpu_usage(interval: float = 1.0) -> list[float]:
    """Return per‑core CPU usage as a list of floats (0‑100)."""
    if _PSUTIL_AVAILABLE and psutil:
        try:
            return list(psutil.cpu_percent(interval=interval, percpu=True))
        except OSError as exc:
            logger.debug("psutil cpu_percent percpu failed: %s", exc)
    return []


def get_cpu_count() -> int:
    """Return the number of logical CPUs."""
    if _PSUTIL_AVAILABLE and psutil:
        count = _get_cpu_count_psutil()
        if count is not None:
            return count
    return os.cpu_count() or 1


def _get_cpu_count_psutil() -> int | None:
    try:
        count = psutil.cpu_count(logical=True)
        return int(count) if count is not None else None
    except OSError as exc:
        logger.debug("psutil cpu_count failed: %s", exc)
        return None


def get_physical_cpu_count() -> int:
    """Return the number of physical CPU cores."""
    if _PSUTIL_AVAILABLE and psutil:
        try:
            return int(psutil.cpu_count(logical=False) or 1)
        except OSError as exc:
            logger.debug("psutil cpu_count physical failed: %s", exc)
    return get_cpu_count()


def get_cpu_frequency() -> dict[str, Any]:
    """Return current CPU frequency info."""
    if _PSUTIL_AVAILABLE and psutil:
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    "current": float(freq.current),
                    "min": float(freq.min),
                    "max": float(freq.max),
                }
        except OSError as exc:
            logger.debug("psutil cpu_freq failed: %s", exc)
    return {}


def get_load_average() -> tuple[float, float, float]:
    """Return the 1, 5, 15 minute load averages (Linux/Android)."""
    if _PSUTIL_AVAILABLE and psutil and hasattr(psutil, "getloadavg"):
        avg = _get_load_average_psutil()
        if avg:
            return avg
    return _get_load_average_fallback()


def _get_load_average_psutil() -> tuple[float, float, float] | None:
    try:
        avg = psutil.getloadavg()
        return (float(avg[0]), float(avg[1]), float(avg[2]))
    except (OSError, AttributeError, IndexError) as exc:
        logger.debug("psutil getloadavg failed: %s", exc)
        return None


def _get_load_average_fallback() -> tuple[float, float, float]:
    try:
        with open("/proc/loadavg", encoding="utf-8") as f:
            parts = f.read().strip().split()
            if len(parts) >= 3:
                return (float(parts[0]), float(parts[1]), float(parts[2]))
    except OSError as exc:
        logger.debug("/proc/loadavg read failed: %s", exc)
    return (0.0, 0.0, 0.0)


# --- Disk Metrics (formerly disk.py) ---


def get_disk_usage(path: str | Path = "/") -> dict[str, float]:
    """Return disk usage for *path* (total, used, free, percent)."""
    target = str(path)

    # Try psutil first
    if _PSUTIL_AVAILABLE and psutil:
        usage = _get_disk_usage_psutil(target)
        if usage:
            return usage

    # Fallback using shutil
    return _get_disk_usage_shutil(target)


def _get_disk_usage_psutil(target: str) -> dict[str, float] | None:
    try:
        usage = psutil.disk_usage(target)
        return {
            "total": float(usage.total),
            "used": float(usage.used),
            "free": float(usage.free),
            "percent": usage.percent,
        }
    except OSError as exc:
        logger.debug("psutil disk_usage failed: %s", exc)
        return None


def _get_disk_usage_shutil(target: str) -> dict[str, float]:
    disk = {"total": 0.0, "used": 0.0, "free": 0.0, "percent": 0.0}
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


# --- Memory Metrics (formerly memory.py) ---


def get_memory_usage() -> dict[str, float]:
    """Return a dict with ``total``, ``available``, ``percent``, ``used`` bytes."""
    if _PSUTIL_AVAILABLE and psutil:
        mem = _get_memory_usage_psutil()
        if mem:
            return mem
    return _get_memory_usage_fallback()


def _get_memory_usage_psutil() -> dict[str, float] | None:
    try:
        mem = psutil.virtual_memory()
        return {
            "total": float(mem.total),
            "available": float(mem.available),
            "percent": mem.percent,
            "used": float(mem.used),
        }
    except OSError as exc:
        logger.debug("psutil virtual_memory failed: %s", exc)
        return None


def _get_memory_usage_fallback() -> dict[str, float]:
    mem_info = {"total": 0.0, "available": 0.0, "percent": 0.0, "used": 0.0}
    try:
        results = _read_meminfo(["MemTotal", "MemAvailable"])
        mem_total = results.get("MemTotal", 0)
        mem_avail = results.get("MemAvailable", 0)
        if mem_total > 0:
            used = mem_total - mem_avail
            mem_info.update(
                {
                    "total": float(mem_total),
                    "available": float(mem_avail),
                    "percent": (used / mem_total) * 100.0,
                    "used": float(used),
                }
            )
    except OSError as exc:
        logger.debug("/proc/meminfo read failed: %s", exc)
    return mem_info


def get_swap_usage() -> dict[str, float]:
    """Return swap memory info."""
    if _PSUTIL_AVAILABLE and psutil:
        swap = _get_swap_usage_psutil()
        if swap:
            return swap
    return _get_swap_usage_fallback()


def _get_swap_usage_psutil() -> dict[str, float] | None:
    try:
        swap = psutil.swap_memory()
        return {
            "total": float(swap.total),
            "used": float(swap.used),
            "percent": swap.percent,
        }
    except OSError as exc:
        logger.debug("psutil swap_memory failed: %s", exc)
        return None


def _get_swap_usage_fallback() -> dict[str, float]:
    swap_info = {"total": 0.0, "used": 0.0, "percent": 0.0}
    try:
        results = _read_meminfo(["SwapTotal", "SwapFree"])
        total = results.get("SwapTotal", 0)
        free = results.get("SwapFree", 0)
        if total > 0:
            used = total - free
            swap_info.update(
                {
                    "total": float(total),
                    "used": float(used),
                    "percent": (used / total) * 100.0,
                }
            )
    except OSError as exc:
        logger.debug("/proc/meminfo read failed: %s", exc)
    return swap_info


def _read_meminfo(keys: list[str]) -> dict[str, int]:
    results = {key: 0 for key in keys}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                _parse_meminfo_line(line, results)
    except OSError as exc:
        logger.debug("/proc/meminfo read failed: %s", exc)
    return results


def _parse_meminfo_line(line: str, results: dict[str, int]) -> None:
    parts = line.split()
    if not parts:
        return
    key = parts[0].replace(":", "")
    if key in results:
        results[key] = int(parts[1]) * 1024


# --- Battery Metrics (formerly battery.py) ---


def get_battery_status() -> dict[str, Any]:
    """Return battery information (percent, power_plugged, time_left)."""
    battery: dict[str, Any] = {}
    if _PSUTIL_AVAILABLE and psutil:
        bat = _get_battery_status_psutil()
        if bat:
            battery.update(bat)

    # Android fallback
    fallback = _get_battery_status_fallback()
    _merge_battery_data(battery, fallback)

    return battery


def _merge_battery_data(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if key not in target:
            target[key] = value


def _get_battery_status_psutil() -> dict[str, Any] | None:
    try:
        bat = psutil.sensors_battery()
        if bat:
            return {
                "percent": bat.percent,
                "power_plugged": bat.power_plugged,
                "secsleft": bat.secsleft,
            }
    except OSError as exc:
        logger.debug("psutil sensors_battery failed: %s", exc)
    return None


def _get_battery_status_fallback() -> dict[str, Any]:
    battery = {}
    try:
        base = Path("/sys/class/power_supply/battery")
        if base.is_dir():
            capacity = _read_int(base / "capacity")
            status_file = base / "status"
            status = status_file.read_text().strip() if status_file.is_file() else ""

            battery["percent"] = capacity if capacity is not None else 0
            battery["power_plugged"] = status.lower() in ("charging", "full")
            battery["secsleft"] = -1
    except OSError as exc:
        logger.debug("Battery fallback failed: %s", exc)
    return battery


def _read_int(path: Path) -> int | None:
    if path.is_file():
        try:
            return int(path.read_text().strip())
        except (OSError, ValueError):
            pass
    return None


# --- Temperatures (formerly temperatures.py) ---


def get_temperatures() -> dict[str, float]:
    """Return a dict of sensor names and their temperatures in °C."""
    # Try psutil
    if _PSUTIL_AVAILABLE and psutil:
        temps = _get_temperatures_psutil()
        if temps:
            return temps

    # Fallback to thermal zones
    return _get_temperatures_fallback()


def _get_temperatures_psutil() -> dict[str, float]:
    temps: dict[str, float] = {}
    try:
        sensors = psutil.sensors_temperatures()
        for name, entries in sensors.items():
            for entry in entries:
                temps[entry.label or name] = entry.current
    except OSError as exc:
        logger.debug("psutil sensors_temperatures failed: %s", exc)
    return temps


def _get_temperatures_fallback() -> dict[str, float]:
    temps: dict[str, float] = {}
    try:
        base = Path("/sys/class/thermal")
        if base.exists():
            _collect_thermal_zones(base, temps)
    except OSError as exc:
        logger.debug("Thermal zone lookup failed: %s", exc)
    return temps


def _collect_thermal_zones(base: Path, temps: dict[str, float]) -> None:
    for zone in base.iterdir():
        if zone.is_dir() and zone.name.startswith("thermal_zone"):
            _process_thermal_zone(zone, temps)


def _process_thermal_zone(zone: Path, temps: dict[str, float]) -> None:
    type_p, temp_p = zone / "type", zone / "temp"
    if type_p.is_file() and temp_p.is_file():
        try:
            temp = float(temp_p.read_text().strip()) / 1000.0
            temps[type_p.read_text().strip()] = temp
        except (OSError, ValueError):
            pass


# --- New Class-Based Monitors ---


class CPUMonitor:
    """Monitor CPU metrics."""

    @staticmethod
    def get_usage(interval: float = 1.0) -> float:
        return get_cpu_usage(interval=interval)

    @staticmethod
    def get_per_core_usage(interval: float = 1.0) -> list[float]:
        return get_per_cpu_usage(interval=interval)

    @staticmethod
    def get_count(logical: bool = True) -> int:
        return get_cpu_count() if logical else get_physical_cpu_count()

    @staticmethod
    def get_frequency() -> dict[str, Any]:
        return get_cpu_frequency()

    @staticmethod
    def get_load_average() -> tuple[float, float, float]:
        return get_load_average()


class MemoryMonitor:
    """Monitor memory metrics."""

    @staticmethod
    def get_usage() -> dict[str, float]:
        return get_memory_usage()

    @staticmethod
    def get_swap_usage() -> dict[str, float]:
        return get_swap_usage()


class DiskMonitor:
    """Monitor disk metrics."""

    @staticmethod
    def get_usage(path: str = "/") -> dict[str, float]:
        return get_disk_usage(path=path)


class BatteryMonitor:
    """Monitor battery metrics."""

    @staticmethod
    def get_status() -> dict[str, Any]:
        return get_battery_status()


class EnvironmentMonitor:
    """Monitor environment and system info."""

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "name": get_environment_name(),
            "os": get_os(),
            "os_version": get_os_version(),
            "architecture": get_architecture(),
            "python_version": get_python_version(),
            "hostname": get_hostname(),
            "uptime_seconds": get_uptime_seconds(),
        }


class SystemMonitor:
    """Unified system monitor."""

    def __init__(self) -> None:
        self.cpu = CPUMonitor()
        self.memory = MemoryMonitor()
        self.disk = DiskMonitor()
        self.battery = BatteryMonitor()
        self.env = EnvironmentMonitor()

    def get_full_report(self) -> dict[str, Any]:
        """Return a comprehensive report."""
        return {
            "environment": self.env.get_info(),
            "cpu": {
                "usage_percent": self.cpu.get_usage(),
                "per_cpu_usage": self.cpu.get_per_core_usage(),
                "count": self.cpu.get_count(),
                "physical_count": self.cpu.get_count(logical=False),
                "frequency": self.cpu.get_frequency(),
                "load_average": self.cpu.get_load_average(),
            },
            "memory": {
                "virtual": self.memory.get_usage(),
                "swap": self.memory.get_swap_usage(),
            },
            "disk": {
                "root": self.disk.get_usage(),
            },
            "temperatures": get_temperatures(),
            "battery": self.battery.get_status(),
        }


def get_uptime_seconds() -> float:
    """Return system uptime in seconds, or 0.0 if unknown."""
    if _PSUTIL_AVAILABLE and psutil:
        try:
            return float(time.time() - psutil.boot_time())
        except OSError as exc:
            logger.debug("psutil boot_time failed: %s", exc)
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            return float(f.readline().split()[0])
    except (OSError, ValueError) as exc:
        logger.debug("/proc/uptime read failed: %s", exc)
    return 0.0
