"""Cross‑platform system information utilities – Android, Termux, Linux, and more."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from sota_dl.infrastructure import system_monitor as sm

_PSUTIL_AVAILABLE = sm._PSUTIL_AVAILABLE
psutil = sm.psutil

logger = logging.getLogger(__name__)


class SystemInfoError(Exception):
    """Base exception for system information retrieval failures."""


# pylint: disable=too-many-public-methods
class SystemInfo:
    """
    Gather system metrics reliably across Linux, Android, and Termux.

    All methods are static and safe to call even when optional dependencies
    (like ``sm.psutil``) are missing – they return sensible defaults or raise
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
        return sm.is_linux()

    @staticmethod
    def is_android() -> bool:
        """
        Return ``True`` if running on Android.

        Checks several indicators: ``ANDROID_ROOT``, ``TERMUX_VERSION``, or
        Android‑specific build properties.
        """
        return sm.is_android()

    @staticmethod
    def is_termux() -> bool:
        """Return ``True`` if running inside Termux."""
        return sm.is_termux()

    @staticmethod
    def get_environment_name() -> str:
        """Return a human‑readable environment name."""
        return sm.get_environment_name()

    # ------------------------------------------------------------------
    # OS & Python info
    # ------------------------------------------------------------------
    @staticmethod
    def get_os() -> str:
        """Return the operating system name (e.g. 'Linux', 'Windows')."""
        return sm.get_os()

    @staticmethod
    def get_os_version() -> str:
        """Return OS version string."""
        return sm.get_os_version()

    @staticmethod
    def get_architecture() -> str:
        """Return machine architecture (e.g. 'x86_64', 'aarch64')."""
        return sm.get_architecture()

    @staticmethod
    def get_python_version() -> str:
        """Return the Python version string."""
        return sm.get_python_version()

    @staticmethod
    def get_hostname() -> str:
        """Return the system hostname."""
        return sm.get_hostname()

    # ------------------------------------------------------------------
    # CPU
    # ------------------------------------------------------------------
    @staticmethod
    def get_cpu_usage(interval: float = 1.0) -> float:
        """
        Return overall CPU usage percent (0‑100).

        Args:
            interval: Seconds to measure over.
            Ignored if sm.psutil unavailable.

        Returns:
            CPU utilisation as a float, or -1.0 if not measurable.
        """
        return sm.get_cpu_usage(interval=interval)

    @staticmethod
    def get_per_cpu_usage(interval: float = 1.0) -> list[float]:
        """
        Return per‑core CPU usage as a list of floats (0‑100).

        Returns an empty list if sm.psutil is unavailable.
        """
        return sm.get_per_cpu_usage(interval=interval)

    @staticmethod
    def get_cpu_count() -> int:
        """Return the number of logical CPUs."""
        return sm.get_cpu_count()

    @staticmethod
    def get_physical_cpu_count() -> int:
        """Return the number of physical CPU cores."""
        return sm.get_physical_cpu_count()

    @staticmethod
    def get_cpu_frequency() -> dict[str, Any]:
        """
        Return current CPU frequency info.

        Returns a dict with keys ``current``, ``min``, ``max`` (MHz) or empty.
        """
        return sm.get_cpu_frequency()

    @staticmethod
    def get_load_average() -> tuple[float, float, float]:
        """Return the 1, 5, 15 minute load averages (Linux/Android)."""
        return sm.get_load_average()

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------
    @staticmethod
    def get_memory_usage() -> dict[str, float]:
        """
        Return a dict with ``total``, ``available``, ``percent``, ``used`` bytes.

        Returns zeroes if information cannot be obtained.
        """
        return sm.get_memory_usage()

    @staticmethod
    def get_swap_usage() -> dict[str, float]:
        """Return swap memory info (total, used, percent) or zeroes."""
        return sm.get_swap_usage()

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
        return sm.get_disk_usage(path=path)

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
        return sm.get_temperatures()

    # ------------------------------------------------------------------
    # Battery
    # ------------------------------------------------------------------
    @staticmethod
    def get_battery_status() -> dict[str, Any]:
        """
        Return battery information (percent, power_plugged, time_left).

        Returns empty dict if no battery is present or info is unavailable.
        """
        return sm.get_battery_status()

    # ------------------------------------------------------------------
    # Uptime
    # ------------------------------------------------------------------
    @staticmethod
    def get_uptime_seconds() -> float:
        """Return system uptime in seconds, or 0.0 if unknown."""
        return sm.get_uptime_seconds()

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
