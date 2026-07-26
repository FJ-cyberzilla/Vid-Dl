from unittest.mock import MagicMock
from core.fallback import FallbackDownloader
from core.protocols import DownloadOptions, DownloadResult, DownloadStatus


def test_fallback_success() -> None:
    backend1 = MagicMock()
    backend1.download.side_effect = ValueError("Fail")

    backend2 = MagicMock()
    success_result = DownloadResult(status=DownloadStatus.COMPLETED)
    backend2.download.return_value = success_result

    downloader = FallbackDownloader([backend1, backend2])

    result = downloader.download("http://...", DownloadOptions(), lambda x: None)

    assert result.status == DownloadStatus.COMPLETED
    assert backend1.download.called
    assert backend2.download.called


def test_fallback_all_fail() -> None:
    backend1 = MagicMock()
    backend1.download.side_effect = OSError("Fail 1")

    backend2 = MagicMock()
    backend2.download.side_effect = ValueError("Fail 2")

    downloader = FallbackDownloader([backend1, backend2])

    result = downloader.download("http://...", DownloadOptions(), lambda x: None)

    assert result.status == DownloadStatus.FAILED
    assert result.error is not None
    assert "Fail 2" in result.error
