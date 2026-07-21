import pytest
from unittest.mock import MagicMock
from core.download_manager import SOTADownloadManager
from core.protocols import DownloadOptions, DownloadResult, DownloadStatus
from core.fallback import FallbackDownloader
from core.controller import DownloadController


class TestSOTADownloadManager:
    @pytest.fixture
    def mock_downloader(self):
        return MagicMock(spec=FallbackDownloader)

    @pytest.fixture
    def mock_controller(self):
        return MagicMock(spec=DownloadController)

    @pytest.fixture
    def manager(self, mock_downloader, mock_controller):
        return SOTADownloadManager(mock_downloader, mock_controller)

    def test_execute_dry_run(self, manager, mock_downloader):
        options = DownloadOptions(dry_run=True)
        result = manager.execute("https://example.com", options=options)

        assert result.status == DownloadStatus.COMPLETED
        assert result.metadata["dry_run"] is True
        mock_downloader.download.assert_not_called()

    def test_execute_success(self, manager, mock_downloader, mock_controller):
        # Setup mock progress reporter
        mock_progress = MagicMock()
        mock_controller.progress_reporter = mock_progress

        # Setup mock result
        success_result = DownloadResult(status=DownloadStatus.COMPLETED)
        mock_downloader.download.return_value = success_result

        target = "https://example.com"
        result = manager.execute(target)

        assert result.status == DownloadStatus.COMPLETED
        mock_downloader.download.assert_called_once()
        mock_controller.reset.assert_called_once()

    def test_lifecycle_methods(self, manager, mock_controller):
        manager.cancel()
        mock_controller.cancel.assert_called_once()

        manager.pause()
        mock_controller.pause.assert_called_once()

        manager.resume()
        mock_controller.resume.assert_called_once()

    def test_progress_hook_downloading(self, manager, mock_controller):
        mock_progress = MagicMock()
        mock_controller.progress_reporter = mock_progress
        mock_controller.current_task_id = "task1"

        data = {
            "status": "downloading",
            "total_bytes": 100,
            "downloaded_bytes": 50,
            "filename": "test.mp4",
        }

        manager._progress_hook(data)

        mock_controller.check_state.assert_called_once()
        mock_progress.update.assert_called_once()

    def test_progress_hook_finished(self, manager, mock_controller):
        mock_progress = MagicMock()
        mock_controller.progress_reporter = mock_progress
        mock_controller.current_task_id = "task1"

        data = {"status": "finished"}

        manager._progress_hook(data)

        mock_progress.update.assert_called_once()
