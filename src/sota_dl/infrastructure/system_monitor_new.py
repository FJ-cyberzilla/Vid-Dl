"""System metrics and environment monitoring component."""

from __future__ import annotations

import logging
from typing import Any

from sota_dl.infrastructure import system_monitor as sm

logger = logging.getLogger(__name__)


class CPUMonitor:
    """Monitor CPU metrics."""

    @staticmethod
    def get_usage(interval: float = 1.0) -> float:
        return sm.get_cpu_usage(interval=interval)

    @staticmethod
    def get_per_core_usage(interval: float = 1.0) -> list[float]:
        return sm.get_per_cpu_usage(interval=interval)

    @staticmethod
    def get_count(logical: bool = True) -> int:
        return sm.get_cpu_count() if logical else sm.get_physical_cpu_count()

    @staticmethod
    def get_frequency() -> dict[str, Any]:
        return sm.get_cpu_frequency()

    @staticmethod
    def get_load_average() -> tuple[float, float, float]:
        return sm.get_load_average()


class MemoryMonitor:
    """Monitor memory metrics."""

    @staticmethod
    def get_usage() -> dict[str, float]:
        return sm.get_memory_usage()

    @staticmethod
    def get_swap_usage() -> dict[str, float]:
        return sm.get_swap_usage()


class DiskMonitor:
    """Monitor disk metrics."""

    @staticmethod
    def get_usage(path: str = "/") -> dict[str, float]:
        return sm.get_disk_usage(path=path)


class BatteryMonitor:
    """Monitor battery metrics."""

    @staticmethod
    def get_status() -> dict[str, Any]:
        return sm.get_battery_status()


class EnvironmentMonitor:
    """Monitor environment and system info."""

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "name": sm.get_environment_name(),
            "os": sm.get_os(),
            "os_version": sm.get_os_version(),
            "architecture": sm.get_architecture(),
            "python_version": sm.get_python_version(),
            "hostname": sm.get_hostname(),
            "uptime_seconds": sm.get_uptime_seconds(),
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
            "temperatures": sm.get_temperatures(),
            "battery": self.battery.get_status(),
        }
