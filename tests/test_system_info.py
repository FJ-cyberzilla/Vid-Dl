import os
from pathlib import Path
from typing import Any
from unittest.mock import patch, mock_open, MagicMock
from infrastructure.system import SystemInfo


def test_environment_detection() -> None:
    with patch("platform.system", return_value="Linux"):
        assert SystemInfo.is_linux() is True

    with patch("platform.system", return_value="Windows"):
        assert SystemInfo.is_linux() is False

    with patch("infrastructure.system_components.env.is_linux", return_value=True):
        with patch.dict(os.environ, {"TERMUX_VERSION": "0.118"}):
            assert SystemInfo.is_termux() is True
            assert SystemInfo.is_android() is True
            assert SystemInfo.get_environment_name() == "Termux (Android)"

        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                assert SystemInfo.is_android() is True
                assert SystemInfo.get_environment_name() == "Android"

            with (
                patch("pathlib.Path.exists", return_value=False),
                patch.dict(os.environ, {"ANDROID_ROOT": "/system"}),
            ):
                assert SystemInfo.is_android() is True


def test_os_info() -> None:
    with patch("platform.system", return_value="Linux"):
        assert SystemInfo.get_os() == "Linux"
    with patch("platform.version", return_value="5.10.0"):
        assert SystemInfo.get_os_version() == "5.10.0"
    with patch("platform.machine", return_value="x86_64"):
        assert SystemInfo.get_architecture() == "x86_64"


def test_cpu_usage_no_psutil() -> None:
    with patch(
        "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
    ):
        assert SystemInfo.get_cpu_usage() == -1.0
        assert SystemInfo.get_per_cpu_usage() == []


def test_cpu_usage_with_psutil() -> None:
    with patch(
        "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", True
    ):
        with patch("psutil.cpu_percent", return_value=50.0):
            assert SystemInfo.get_cpu_usage() == 50.0
        with patch("psutil.cpu_percent", return_value=[40.0, 60.0]):
            assert SystemInfo.get_per_cpu_usage() == [40.0, 60.0]


def test_cpu_count() -> None:
    with (
        patch("infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", True),
        patch("psutil.cpu_count", return_value=4),
    ):
        assert SystemInfo.get_cpu_count() == 4

    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("os.cpu_count", return_value=2),
    ):
        assert SystemInfo.get_cpu_count() == 2


def test_load_average_fallback() -> None:
    mock_data = "0.10 0.20 0.30 1/100 1234"
    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("builtins.open", mock_open(read_data=mock_data)),
    ):
        assert SystemInfo.get_load_average() == (0.1, 0.2, 0.3)


def test_memory_usage_fallback() -> None:
    mock_data = "MemTotal: 1000000 kB\nMemAvailable: 400000 kB\n"
    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("builtins.open", mock_open(read_data=mock_data)),
    ):
        mem = SystemInfo.get_memory_usage()
        assert mem["total"] == 1000000 * 1024
        assert mem["available"] == 400000 * 1024
        assert mem["percent"] == 60.0


def test_disk_usage_fallback() -> None:
    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("shutil.disk_usage") as mock_disk,
    ):
        mock_disk.return_value = MagicMock(total=1000, used=400, free=600)
        usage = SystemInfo.get_disk_usage("/")
        assert usage["total"] == 1000
        assert usage["percent"] == 40.0


def test_temperatures_fallback(tmp_path: Path) -> None:
    # Create the thermal directory structure under tmp_path
    thermal_dir = tmp_path / "sys" / "class" / "thermal"
    zone_dir = thermal_dir / "thermal_zone0"
    zone_dir.mkdir(parents=True)

    (zone_dir / "type").write_text("cpu-thermal\n", encoding="utf-8")
    (zone_dir / "temp").write_text("45000\n", encoding="utf-8")

    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("infrastructure.system_components.temperatures.Path") as mock_path_cls,
    ):
        # Patch Path("/sys/class/thermal") inside get_temperatures
        # to use our tmp_path thermal_dir
        def path_side_effect(*args: Any, **kwargs: Any) -> Path:
            if args and args[0] == "/sys/class/thermal":
                return thermal_dir
            return Path(*args, **kwargs)

        mock_path_cls.side_effect = path_side_effect

        temps = SystemInfo.get_temperatures()
        assert temps["cpu-thermal"] == 45.0


def test_battery_fallback() -> None:
    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("pathlib.Path.is_dir", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.read_text") as mock_read,
    ):
        mock_read.side_effect = ["80", "Charging"]
        bat = SystemInfo.get_battery_status()
        assert bat["percent"] == 80
        assert bat["power_plugged"] is True


def test_uptime_fallback() -> None:
    with (
        patch(
            "infrastructure.system_components.psutil_helper._PSUTIL_AVAILABLE", False
        ),
        patch("builtins.open", mock_open(read_data="12345.67 89012.34")),
    ):
        assert SystemInfo.get_uptime_seconds() == 12345.67


def test_full_report() -> None:
    # Mock psutil.swap_memory if available to avoid Permission denied on
    # /proc/vmstat under Android
    from infrastructure.system import _PSUTIL_AVAILABLE

    if _PSUTIL_AVAILABLE:
        with patch("psutil.swap_memory") as mock_swap:
            mock_swap.return_value = MagicMock(
                total=1000, used=200, free=800, percent=20.0
            )
            report = SystemInfo.get_full_report()
    else:
        report = SystemInfo.get_full_report()

    assert "environment" in report
    assert "cpu" in report
    assert "memory" in report
    assert "disk" in report
