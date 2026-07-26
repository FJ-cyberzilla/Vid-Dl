import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from config.settings import get_download_path, check_ffmpeg, _is_writable


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    d = tmp_path / "writable_dir"
    d.mkdir()
    return d


def test_is_writable_success(temp_dir: Path) -> None:
    assert _is_writable(temp_dir) is True


def test_is_writable_failure() -> None:
    # A path that shouldn't be writable (e.g., read-only file)
    path = Path("/root/test")
    # This might behave differently depending on OS, but generally should fail
    # We can also mock if needed.
    assert _is_writable(path) is False


@patch("config.settings._is_writable")
@patch("config.settings.ENV_OVERRIDE", None)
@patch("config.settings.ANDROID_GALLERY_DIR", Path("/fake/android"))
@patch("config.settings.TERMUX_FALLBACK", Path("/fake/termux"))
@patch("config.settings.LOCAL_FALLBACK", Path("./downloads"))
def test_get_download_path_priority(mock_is_writable: MagicMock) -> None:
    # Setup mock to return False for everything, forcing local fallback
    mock_is_writable.return_value = False

    # Path is absolute, this might create ./downloads in test dir
    path = get_download_path()
    assert path.name == "downloads"


@patch("shutil.which")
@patch("subprocess.run")
def test_check_ffmpeg_found(mock_run: MagicMock, mock_which: MagicMock) -> None:
    mock_which.return_value = "/usr/bin/ffmpeg"
    mock_run.return_value = MagicMock(returncode=0, stdout="ffmpeg version 4.4.2")

    assert check_ffmpeg(version_check=True) is True
    mock_run.assert_called_once()


@patch("shutil.which")
def test_check_ffmpeg_not_found(mock_which: MagicMock) -> None:
    mock_which.return_value = None
    assert check_ffmpeg() is False
