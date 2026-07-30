"""Composition root for SOTA Downloader."""

from sota_dl.core.download_service import DownloadService
from sota_dl.core.event_bus import EventBus
from sota_dl.core.fallback import FallbackDownloader
from sota_dl.core.protocols import ProgressReporter
from sota_dl.infrastructure.adapters.yt_dlp import YtDlpAdapter
from sota_dl.ui.progress_bars import get_sota_progress


def create_sota_manager(
    event_bus: EventBus,
    progress_reporter: ProgressReporter | None = None,
) -> DownloadService:
    """Factory to create a fully configured DownloadService."""
    downloader = FallbackDownloader(backends=[YtDlpAdapter()])
    return DownloadService(
        downloader_backend=downloader,
        progress_reporter=progress_reporter or get_sota_progress(),
        event_bus=event_bus,
    )
