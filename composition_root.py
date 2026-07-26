"""Composition root for SOTA Downloader."""

from core.download_manager import SOTADownloadManager
from core.controller import DownloadController
from core.fallback import FallbackDownloader
from core.protocols import ProgressReporter
from infrastructure.adapters.yt_dlp import YtDlpBackend
from ui.progress_bars import get_sota_progress


def create_sota_manager(
    progress_reporter: ProgressReporter | None = None,
) -> SOTADownloadManager:
    """Factory to create a fully configured SOTADownloadManager."""
    downloader = FallbackDownloader(backends=[YtDlpBackend()])
    controller = DownloadController(progress_reporter or get_sota_progress())
    return SOTADownloadManager(downloader, controller)
