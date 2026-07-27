from pathlib import Path
from typing import Any
import pytest
import threading
from unittest.mock import MagicMock, patch
from sota_dl.core.download_service import DownloadService
from sota_dl.core.protocols import DownloadOptions, DownloadResult, DownloadStatus


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock()
    # Mock default state for the controller
    controller.cancelled = False
    controller.pause_event = threading.Event()
    controller.pause_event.set()
    return controller


@pytest.fixture
def service(mock_downloader: MagicMock, mock_controller: MagicMock) -> DownloadService:
    return DownloadService(downloader=mock_downloader, controller=mock_controller)


def test_process_single_target_success(
    service: DownloadService, mock_downloader: MagicMock
) -> None:
    mock_downloader.execute.return_value = DownloadResult(
        status=DownloadStatus.COMPLETED
    )

    results = service.process_target("https://example.com")

    assert len(results) == 1
    assert results[0].status == DownloadStatus.COMPLETED
    mock_downloader.execute.assert_called_once_with(
        "https://example.com", service.default_options
    )


def test_process_target_failure(
    service: DownloadService, mock_downloader: MagicMock
) -> None:
    # Mock exception in downloader
    mock_downloader.execute.side_effect = ValueError("Config error")

    results = service.process_target("https://example.com")

    assert len(results) == 1
    assert results[0].status == DownloadStatus.FAILED
    assert results[0].error is not None
    assert "Config error" in results[0].error


def test_resolve_targets_file(service: DownloadService, tmp_path: Path) -> None:
    batch_file = tmp_path / "urls.txt"
    batch_file.write_text("https://a.com\n#comment\n\nhttps://b.com")

    targets = service._resolve_targets(str(batch_file))
    assert targets == ["https://a.com", "https://b.com"]


def test_cancel_operation(
    service: DownloadService,
    mock_downloader: MagicMock,
    mock_controller: MagicMock,
) -> None:
    # Setup mock to simulate a slow long-running process
    import time
    
    def slow_execute(*args: Any, **kwargs: Any) -> DownloadResult:
        time.sleep(0.1)
        return DownloadResult(status=DownloadStatus.COMPLETED)
    
    mock_downloader.execute.side_effect = slow_execute
    
    # Simulate cancellation in the controller
    def side_effect_cancel():
        mock_controller.cancelled = True
        
    mock_controller.cancel.side_effect = side_effect_cancel
    
    # Trigger cancellation in a separate thread
    threading.Timer(0.05, service.cancel).start()
    
    # Process multiple targets
    with patch.object(
        service, "_resolve_targets", return_value=["url1", "url2", "url3"]
    ):
        results = service.process_target("dummy", options=DownloadOptions())
    
    assert len(results) < 3
    assert mock_controller.cancelled


def test_pause_resume_operation(
    service: DownloadService, mock_downloader: MagicMock
) -> None:
    mock_downloader.execute.return_value = DownloadResult(
        status=DownloadStatus.COMPLETED
    )

    # Pause initially
    service.pause()

    # Resume in a thread
    threading.Timer(0.1, service.resume).start()

    # This should block then proceed
    results = service.process_target("https://a.com")
    assert len(results) == 1


def test_empty_batch_file_raises(service: DownloadService, tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    with pytest.raises(ValueError, match="no valid URLs"):
        service._resolve_targets(str(empty_file))


def test_downloader_progress_reporter_init(
    mock_downloader: MagicMock, mock_controller: MagicMock
) -> None:
    mock_reporter = MagicMock()
    mock_downloader.progress_reporter = None
    DownloadService(
        downloader=mock_downloader,
        controller=mock_controller,
        progress_reporter=mock_reporter,
    )

    assert mock_downloader.progress_reporter == mock_reporter
