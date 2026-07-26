"""Composition root for SOTA Downloader."""

from core.download_manager import SOTADownloadManager
from core.controller import DownloadController
from core.fallback import FallbackDownloader
from core.protocols import ProgressReporter
from core.event_bus import EventBus
from infrastructure.adapters.yt_dlp import YtDlpAdapter
from ui.progress_bars import get_sota_progress


def create_sota_manager(
    progress_reporter: ProgressReporter | None = None,
    event_bus: EventBus | None = None,
) -> SOTADownloadManager:
    """Factory to create a fully configured SOTADownloadManager."""
    downloader = FallbackDownloader(backends=[YtDlpAdapter()])
    controller = DownloadController(progress_reporter or get_sota_progress())
    return SOTADownloadManager(downloader, controller, event_bus=event_bus)
