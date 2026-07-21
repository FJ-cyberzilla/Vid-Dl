from unittest.mock import patch
from infrastructure.system import SystemInfo

def test_environment_detection():
    # Since we can't easily change the OS, we just check if it runs
    assert isinstance(SystemInfo.is_linux(), bool)
    assert isinstance(SystemInfo.is_android(), bool)
    assert isinstance(SystemInfo.is_termux(), bool)
    assert isinstance(SystemInfo.get_environment_name(), str)

def test_basic_info():
    assert isinstance(SystemInfo.get_os(), str)
    assert isinstance(SystemInfo.get_os_version(), str)
    assert isinstance(SystemInfo.get_architecture(), str)
    assert isinstance(SystemInfo.get_python_version(), str)
    assert isinstance(SystemInfo.get_hostname(), str)

@patch("infrastructure.system._PSUTIL_AVAILABLE", False)
@patch("infrastructure.system.psutil", None)
def test_cpu_usage_no_psutil():
    # Force psutil to be missing
    assert SystemInfo.get_cpu_usage() == -1.0
    assert SystemInfo.get_per_cpu_usage() == []
    assert SystemInfo.get_cpu_count() >= 1

@patch("infrastructure.system._PSUTIL_AVAILABLE", True)
@patch("infrastructure.system.psutil")
def test_cpu_usage_with_psutil(mock_psutil):
    mock_psutil.cpu_percent.return_value = 50.0
    assert SystemInfo.get_cpu_usage() == 50.0
    mock_psutil.cpu_percent.assert_called()

def test_get_memory_usage_fallback():
    # This should trigger the fallback /proc/meminfo read
    mem = SystemInfo.get_memory_usage()
    assert "total" in mem
    assert isinstance(mem["total"], float)
    
@patch("infrastructure.system._PSUTIL_AVAILABLE", False)
@patch("infrastructure.system.psutil", None)
def test_get_uptime_no_psutil():
    # Should try /proc/uptime
    uptime = SystemInfo.get_uptime_seconds()
    assert isinstance(uptime, float)
    assert uptime >= 0.0

@patch("infrastructure.system.psutil")
def test_full_report(mock_psutil):
    # Setup mock for psutil
    mock_psutil.getloadavg.return_value = (0.1, 0.1, 0.1)
    # The rest seem fine, but ensure other used methods are mocked if needed
    mock_psutil.cpu_percent.return_value = 10.0
    
    report = SystemInfo.get_full_report()
    assert "environment" in report
    assert "cpu" in report
    assert "memory" in report
    assert "disk" in report
