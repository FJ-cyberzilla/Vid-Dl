import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from sota_dl.infrastructure.adapters.videodl import VideoDLFallback, InvalidURLError


@pytest.fixture
def downloader() -> VideoDLFallback:
    return VideoDLFallback()


def test_validate_url_success() -> None:
    VideoDLFallback._validate_url("https://example.com/video.mp4")
    VideoDLFallback._validate_url("http://example.com/video.mp4")


def test_validate_url_failure() -> None:
    with pytest.raises(InvalidURLError):
        VideoDLFallback._validate_url("invalid_url")
    with pytest.raises(InvalidURLError):
        VideoDLFallback._validate_url("")


def test_ensure_dir(tmp_path: Path) -> None:
    p = tmp_path / "new_dir" / "file.mp4"
    VideoDLFallback._ensure_dir(p)
    assert p.parent.exists()


@patch("requests.get")
def test_single_download_success(mock_get: MagicMock, tmp_path: Path) -> None:
    dl = VideoDLFallback()
    mock_response = MagicMock()
    mock_response.headers = {"Content-Length": "100"}
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_get.return_value = mock_response

    out = tmp_path / "out.mp4"

    # Mock progress callback
    callback = MagicMock()

    dl._single_download(
        "https://example.com/video.mp4",
        out,
        progress_callback=callback,
        chunk_size=1024,
        timeout=10.0,
    )

    assert out.exists()
    assert out.read_bytes() == b"chunk1chunk2"
    assert callback.call_count == 2
