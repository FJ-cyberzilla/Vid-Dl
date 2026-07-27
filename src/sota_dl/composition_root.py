"""Composition root for SOTA Downloader."""

from sota_dl.core.download_manager import SOTADownloadManager
from sota_dl.core.controller import DownloadController
from sota_dl.core.fallback import FallbackDownloader
from sota_dl.core.protocols import ProgressReporter
from sota_dl.core.event_bus import EventBus
from sota_dl.infrastructure.adapters.yt_dlp import YtDlpAdapter
from sota_dl.ui.progress_bars import get_sota_progress


def create_sota_manager(
    progress_reporter: ProgressReporter | None = None,
    event_bus: EventBus | None = None,
) -> SOTADownloadManager:
    """Factory to create a fully configured SOTADownloadManager."""
    downloader = FallbackDownloader(backends=[YtDlpAdapter()])
    controller = DownloadController(progress_reporter or get_sota_progress())
    return SOTADownloadManager(downloader, controller, event_bus=event_bus)
