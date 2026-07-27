from unittest.mock import patch, MagicMock
from sota_dl.infrastructure.system import SystemInfo


def test_environment_detection() -> None:
    # Since we can't easily change the OS, we just check if it runs
    assert isinstance(SystemInfo.is_linux(), bool)
    assert isinstance(SystemInfo.is_android(), bool)
    assert isinstance(SystemInfo.is_termux(), bool)
    assert isinstance(SystemInfo.get_environment_name(), str)


def test_basic_info() -> None:
    assert isinstance(SystemInfo.get_os(), str)
    assert isinstance(SystemInfo.get_os_version(), str)
    assert isinstance(SystemInfo.get_architecture(), str)
    assert isinstance(SystemInfo.get_python_version(), str)
    assert isinstance(SystemInfo.get_hostname(), str)


@patch("sota_dl.infrastructure.system_monitor._PSUTIL_AVAILABLE", False)
@patch("sota_dl.infrastructure.system_monitor.psutil", None)
def test_cpu_usage_no_psutil() -> None:
    # Force psutil to be missing
    assert SystemInfo.get_cpu_usage() == -1.0
    assert SystemInfo.get_per_cpu_usage() == []
    assert SystemInfo.get_cpu_count() >= 1


@patch("sota_dl.infrastructure.system_monitor._PSUTIL_AVAILABLE", True)
@patch("sota_dl.infrastructure.system_monitor.psutil")
def test_cpu_usage_with_psutil(mock_psutil: MagicMock) -> None:
    mock_psutil.cpu_percent.return_value = 50.0
    assert SystemInfo.get_cpu_usage() == 50.0
    mock_psutil.cpu_percent.assert_called()


def test_get_memory_usage_fallback() -> None:
    # This should trigger the fallback /proc/meminfo read
    mem = SystemInfo.get_memory_usage()
    assert "total" in mem
    assert isinstance(mem["total"], float)


@patch("sota_dl.infrastructure.system_monitor._PSUTIL_AVAILABLE", False)
@patch("sota_dl.infrastructure.system_monitor.psutil", None)
def test_get_uptime_no_psutil() -> None:
    # Should try /proc/uptime
    uptime = SystemInfo.get_uptime_seconds()
    assert isinstance(uptime, float)
    assert uptime >= 0.0


@patch("sota_dl.infrastructure.system_monitor.psutil")
def test_full_report(mock_psutil: MagicMock) -> None:
    # Setup mock for psutil
    mock_psutil.getloadavg.return_value = (0.1, 0.1, 0.1)
    # Handle both cpu usage and per-cpu usage calls
    mock_psutil.cpu_percent.side_effect = lambda interval=None, percpu=False: (
        [10.0] if percpu else 10.0
    )

    report = SystemInfo.get_full_report()
    assert "environment" in report
    assert "cpu" in report
    assert "memory" in report
    assert "disk" in report
