"""Cross‑platform system information utilities – Android, Termux, Linux, and more."""
from __future__ import annotations

import logging
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional dependencies – fall back gracefully if absent
# ---------------------------------------------------------------------------
try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemInfoError(Exception):
    """Base exception for system information retrieval failures."""


# pylint: disable=too-many-public-methods
class SystemInfo:
    """
    Gather system metrics reliably across Linux, Android, and Termux.

    All methods are static and safe to call even when optional dependencies
    (like ``psutil``) are missing – they return sensible defaults or raise
    a specific :class:`SystemInfoError`.

    Usage::

        cpu = SystemInfo.get_cpu_usage()
        mem = SystemInfo.get_memory_usage()
        if SystemInfo.is_android():
            temp = SystemInfo.get_battery_temperature()
    """

    # ------------------------------------------------------------------
    # Environment detection
    # ------------------------------------------------------------------
    @staticmethod
    def is_linux() -> bool:
        """Return ``True`` if running on Linux (including Android)."""
        return platform.system().lower() == "linux"

    @staticmethod
    def is_android() -> bool:
        """
        Return ``True`` if running on Android.

        Checks several indicators: ``ANDROID_ROOT``, ``TERMUX_VERSION``, or
        Android‑specific build properties.
        """
        if not SystemInfo.is_linux():
            return False
        if SystemInfo.is_termux():
            return True
        if os.environ.get("ANDROID_ROOT"):
            return True
        return os.path.exists("/system/build.prop")

    @staticmethod
    def is_termux() -> bool:
        """Return ``True`` if running inside Termux."""
        return os.environ.get("TERMUX_VERSION") is not None

    @staticmethod
    def get_environment_name() -> str:
        """Return a human‑readable environment name."""
        if SystemInfo.is_termux():
            return "Termux (Android)"
        if SystemInfo.is_android():
            return "Android"
        system = platform.system()
        if system == "Linux":
            return "Linux"
        return system

    # ------------------------------------------------------------------
    # OS & Python info
    # ------------------------------------------------------------------
    @staticmethod
    def get_os() -> str:
        """Return the operating system name (e.g. 'Linux', 'Windows')."""
        return platform.system()

    @staticmethod
    def get_os_version() -> str:
        """Return OS version string."""
        return platform.version()

    @staticmethod
    def get_architecture() -> str:
        """Return machine architecture (e.g. 'x86_64', 'aarch64')."""
        return platform.machine()

    @staticmethod
    def get_python_version() -> str:
        """Return the Python version string."""
        return platform.python_version()

    @staticmethod
    def get_hostname() -> str:
        """Return the system hostname."""
        return platform.node()

    # ------------------------------------------------------------------
    # CPU
    # ------------------------------------------------------------------
    @staticmethod
    def get_cpu_usage(interval: float = 1.0) -> float:
        """
        Return overall CPU usage percent (0‑100).

        Args:
            interval: Seconds to measure over. Ignored if psutil unavailable.

        Returns:
            CPU utilisation as a float, or -1.0 if not measurable.
        """
        if _PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_percent(interval=interval)
            except OSError as exc:
                logger.debug("psutil cpu_percent failed: %s", exc)
        return -1.0

    @staticmethod
    def get_per_cpu_usage(interval: float = 1.0) -> list[float]:
        """
        Return per‑core CPU usage as a list of floats (0‑100).

        Returns an empty list if psutil is unavailable.
        """
        if _PSUTIL_AVAILABLE:
            try:
                # Split long line to stay under the limit
                return psutil.cpu_percent(
                    interval=interval, percpu=True
                )  # type: ignore[return-value]
            except OSError as exc:
                logger.debug("psutil cpu_percent percpu failed: %s", exc)
        return []

    @staticmethod
    def get_cpu_count() -> int:
        """Return the number of logical CPUs."""
        if _PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_count(logical=True) or 1
            except OSError as exc:
                logger.debug("psutil cpu_count failed: %s", exc)
        # Fallback: try os.cpu_count()
        try:
            return os.cpu_count() or 1
        except OSError:
            return 1

    @staticmethod
    def get_physical_cpu_count() -> int:
        """Return the number of physical CPU cores."""
        if _PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_count(logical=False) or 1
            except OSError as exc:
                logger.debug("psutil cpu_count physical failed: %s", exc)
        # Fallback: use logical count
        return SystemInfo.get_cpu_count()

    @staticmethod
    def get_cpu_frequency() -> dict[str, Any]:
        """
        Return current CPU frequency info.

        Returns a dict with keys ``current``, ``min``, ``max`` (MHz) or empty.
        """
        if _PSUTIL_AVAILABLE:
            try:
                freq = psutil.cpu_freq()
                if freq:
                    return {
                        "current": freq.current,
                        "min": freq.min,
                        "max": freq.max,
                    }
            except OSError as exc:
                logger.debug("psutil cpu_freq failed: %s", exc)
        return {}

    @staticmethod
    def get_load_average() -> tuple[float, float, float]:
        """Return the 1, 5, 15 minute load averages (Linux/Android)."""
        if _PSUTIL_AVAILABLE:
            try:
                return psutil.getloadavg()  # type: ignore[return-value]
            except OSError as exc:
                logger.debug("psutil getloadavg failed: %s", exc)
        # Fallback: read /proc/loadavg manually
        try:
            with open("/proc/loadavg", encoding="utf-8") as f:
                parts = f.read().strip().split()
                if len(parts) >= 3:
                    return tuple(float(x) for x in parts[:3])  # type: ignore[return-value]
        except OSError as exc:
            logger.debug("/proc/loadavg read failed: %s", exc)
        return (0.0, 0.0, 0.0)

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------
    @staticmethod
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
        if _PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                mem_info.update({
                    "total": float(mem.total),
                    "available": float(mem.available),
                    "percent": mem.percent,
                    "used": float(mem.used),
                })
                return mem_info
            except OSError as exc:
                logger.debug("psutil virtual_memory failed: %s", exc)
        # Fallback via /proc/meminfo (Linux/Android)
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                mem_total = 0
                mem_avail = 0
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        mem_total = int(parts[1]) * 1024  # kB -> bytes
                    elif line.startswith("MemAvailable:"):
                        parts = line.split()
                        mem_avail = int(parts[1]) * 1024
                if mem_total > 0:
                    used = mem_total - mem_avail
                    percent = (used / mem_total) * 100.0
                    mem_info.update({
                        "total": float(mem_total),
                        "available": float(mem_avail),
                        "percent": percent,
                        "used": float(used),
                    })
                    return mem_info
        except OSError as exc:
            logger.debug("/proc/meminfo fallback failed: %s", exc)
        return mem_info

    @staticmethod
    def get_swap_usage() -> dict[str, float]:
        """Return swap memory info (total, used, percent) or zeroes."""
        swap_info = {"total": 0.0, "used": 0.0, "percent": 0.0}
        if _PSUTIL_AVAILABLE:
            try:
                swap = psutil.swap_memory()
                swap_info.update({
                    "total": float(swap.total),
                    "used": float(swap.used),
                    "percent": swap.percent,
                })
                return swap_info
            except OSError as exc:
                logger.debug("psutil swap_memory failed: %s", exc)
        # Fallback via /proc/meminfo
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                total = 0
                free = 0
                for line in f:
                    if line.startswith("SwapTotal:"):
                        parts = line.split()
                        total = int(parts[1]) * 1024
                    elif line.startswith("SwapFree:"):
                        parts = line.split()
                        free = int(parts[1]) * 1024
                if total > 0:
                    used = total - free
                    percent = (used / total) * 100.0
                    swap_info.update({
                        "total": float(total),
                        "used": float(used),
                        "percent": percent,
                    })
        except OSError as exc:
            logger.debug("Swap fallback failed: %s", exc)
        return swap_info

    # ------------------------------------------------------------------
    # Disk
    # ------------------------------------------------------------------
    @staticmethod
    def get_disk_usage(path: str | Path = "/") -> dict[str, float]:
        """
        Return disk usage for *path* (total, used, free, percent).

        Args:
            path: Filesystem path (default root).

        Returns zeroes if unavailable.
        """
        disk = {"total": 0.0, "used": 0.0, "free": 0.0, "percent": 0.0}
        target = str(path)
        if _PSUTIL_AVAILABLE:
            try:
                usage = psutil.disk_usage(target)
                disk.update({
                    "total": float(usage.total),
                    "used": float(usage.used),
                    "free": float(usage.free),
                    "percent": usage.percent,
                })
                return disk
            except OSError as exc:
                logger.debug("psutil disk_usage failed: %s", exc)
        # Fallback: use shutil.disk_usage (Python 3.3+)
        try:
            usage = shutil.disk_usage(target)
            used = float(usage.used)
            total = float(usage.total)
            percent = (used / total) * 100.0 if total > 0 else 0.0
            disk.update({
                "total": total,
                "used": used,
                "free": float(usage.free),
                "percent": percent,
            })
        except OSError as exc:
            logger.debug("shutil.disk_usage fallback failed: %s", exc)
        return disk

    # ------------------------------------------------------------------
    # Temperature
    # ------------------------------------------------------------------
    @staticmethod
    def get_temperatures() -> dict[str, float]:
        """
        Return a dict of sensor names and their temperatures in °C.

        On Linux/Android this may include ``cpu_thermal``, ``battery``, etc.
        Returns an empty dict if not available.
        """
        temps = {}
        if _PSUTIL_AVAILABLE:
            try:
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    for entry in entries:
                        label = entry.label or name
                        temps[label] = entry.current
                return temps
            except OSError as exc:
                logger.debug("psutil sensors_temperatures failed: %s", exc)
        # Manual fallback for Linux thermal zones
        try:
            base = Path("/sys/class/thermal")
            for zone in base.iterdir():
                if zone.is_dir() and zone.name.startswith("thermal_zone"):
                    type_path = zone / "type"
                    temp_path = zone / "temp"
                    if type_path.is_file() and temp_path.is_file():
                        try:
                            type_name = type_path.read_text().strip()
                            temp_str = temp_path.read_text().strip()
                            temp_c = float(temp_str) / 1000.0
                            temps[type_name] = temp_c
                        except (OSError, ValueError) as exc:
                            logger.debug(
                                "Could not read thermal zone %s: %s", zone, exc
                            )
        except OSError as exc:
            logger.debug("Thermal zone fallback failed: %s", exc)
        return temps

    # ------------------------------------------------------------------
    # Battery
    # ------------------------------------------------------------------
    @staticmethod
    def get_battery_status() -> dict[str, Any]:
        """
        Return battery information (percent, power_plugged, time_left).

        Returns empty dict if no battery is present or info is unavailable.
        """
        battery: dict[str, Any] = {}
        if _PSUTIL_AVAILABLE:
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery["percent"] = bat.percent
                    battery["power_plugged"] = bat.power_plugged
                    battery["secsleft"] = bat.secsleft
                    # Do not return early – just update battery and continue
            except OSError as exc:
                logger.debug("psutil sensors_battery failed: %s", exc)

        # Android fallback: /sys/class/power_supply/battery
        try:
            base = Path("/sys/class/power_supply/battery")
            if base.is_dir():
                def read_int(name: str) -> int | None:
                    f = base / name
                    if f.is_file():
                        try:
                            return int(f.read_text().strip())
                        except (OSError, ValueError) as exc:
                            logger.debug(
                                "Failed to read battery %s: %s", name, exc
                            )
                            return None

                capacity = read_int("capacity")
                status_file = base / "status"
                status = (
                    status_file.read_text().strip()
                    if status_file.is_file()
                    else ""
                )
                plugged = status.lower() in ("charging", "full")
                battery["percent"] = capacity if capacity is not None else 0
                battery["power_plugged"] = plugged
                battery["secsleft"] = -1  # not easily available
        except OSError as exc:
            logger.debug("Battery fallback failed: %s", exc)

        return battery

    # ------------------------------------------------------------------
    # Uptime
    # ------------------------------------------------------------------
    @staticmethod
    def get_uptime_seconds() -> float:
        """Return system uptime in seconds, or 0.0 if unknown."""
        if _PSUTIL_AVAILABLE:
            try:
                return time.time() - psutil.boot_time()
            except OSError as exc:
                logger.debug("psutil boot_time failed: %s", exc)
        # Read /proc/uptime (Linux/Android)
        try:
            with open("/proc/uptime", encoding="utf-8") as f:
                return float(f.readline().split()[0])
        except (OSError, ValueError) as exc:
            logger.debug("/proc/uptime read failed: %s", exc)
        return 0.0

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    @staticmethod
    def get_full_report() -> dict[str, Any]:
        """
        Return a comprehensive dictionary with all available system metrics.

        Useful for logging or monitoring dashboards.
        """
        return {
            "environment": {
                "name": SystemInfo.get_environment_name(),
                "os": SystemInfo.get_os(),
                "os_version": SystemInfo.get_os_version(),
                "architecture": SystemInfo.get_architecture(),
                "python_version": SystemInfo.get_python_version(),
                "hostname": SystemInfo.get_hostname(),
            },
            "cpu": {
                "usage_percent": SystemInfo.get_cpu_usage(),
                "per_cpu_usage": SystemInfo.get_per_cpu_usage(),
                "count": SystemInfo.get_cpu_count(),
                "physical_count": SystemInfo.get_physical_cpu_count(),
                "frequency": SystemInfo.get_cpu_frequency(),
                "load_average": SystemInfo.get_load_average(),
            },
            "memory": {
                "virtual": SystemInfo.get_memory_usage(),
                "swap": SystemInfo.get_swap_usage(),
            },
            "disk": {
                "root": SystemInfo.get_disk_usage("/"),
            },
            "temperatures": SystemInfo.get_temperatures(),
            "battery": SystemInfo.get_battery_status(),
            "uptime_seconds": SystemInfo.get_uptime_seconds(),
        }
