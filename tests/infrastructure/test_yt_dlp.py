from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from sota_dl.infrastructure.adapters.yt_dlp import YtDlpEngine, YtDlpError
from yt_dlp.utils import DownloadError


@pytest.fixture
def engine() -> YtDlpEngine:
    return YtDlpEngine(use_aria2c=False)


def test_get_opts_defaults(engine: YtDlpEngine) -> None:
    opts = engine.get_opts()
    assert opts["format"] == "bestvideo+bestaudio/best"
    assert opts["quiet"] is True
    assert "external_downloader" not in opts


def test_get_opts_with_extra(engine: YtDlpEngine) -> None:
    extra = {"foo": "bar"}
    opts = engine.get_opts(extra_opts=extra)
    assert opts["foo"] == "bar"
    assert opts["format"] == "bestvideo+bestaudio/best"


@patch("sota_dl.infrastructure.adapters.yt_dlp.yt_dlp.YoutubeDL")
def test_download_success(
    mock_ydl_class: MagicMock, engine: YtDlpEngine, tmp_path: Path
) -> None:
    # Setup mock to behave like a context manager that holds a mock object
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    # Mock file creation
    final_file = tmp_path / "test.mp4"
    final_file.touch()

    # The engine sets the progress_hooks on the opts dictionary passed to
    # YoutubeDL constructor. We need to capture those opts and invoke the hook
    def side_effect(urls: list[str]) -> None:
        # Capture the opts dictionary used to initialize YoutubeDL
        opts = mock_ydl_class.call_args[0][0]
        # Invoke the progress hook provided in the opts
        hook = opts["progress_hooks"][0]
        hook({"status": "finished", "filename": str(final_file)})

    mock_ydl.download.side_effect = side_effect

    result = engine.download("http://example.com", tmp_path)

    assert result == final_file
    mock_ydl.download.assert_called_once_with(["http://example.com"])


@patch("sota_dl.infrastructure.adapters.yt_dlp.yt_dlp.YoutubeDL")
def test_download_failure(
    mock_ydl_class: MagicMock, engine: YtDlpEngine, tmp_path: Path
) -> None:
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    mock_ydl.download.side_effect = DownloadError("Failed")

    with pytest.raises(YtDlpError, match="Download failed"):
        engine.download("http://example.com", tmp_path)


@patch("sota_dl.infrastructure.adapters.yt_dlp.yt_dlp.YoutubeDL")
def test_download_members_only_error(
    mock_ydl_class: MagicMock, engine: YtDlpEngine, tmp_path: Path
) -> None:
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    mock_ydl.download.side_effect = DownloadError(
        "ERROR: [youtube] RUv4Tz_edN8: This video is available to "
        "this channel's members on level: Newborn"
    )

    with pytest.raises(YtDlpError, match="This is a members-only video"):
        engine.download("http://example.com", tmp_path)


@patch("sota_dl.infrastructure.adapters.yt_dlp.yt_dlp.YoutubeDL")
def test_download_missing_file_error(
    mock_ydl_class: MagicMock, engine: YtDlpEngine, tmp_path: Path
) -> None:
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    # Progress hook doesn't set file, or sets non-existent file

    with pytest.raises(YtDlpError, match="could not be determined"):
        engine.download("http://example.com", tmp_path)
