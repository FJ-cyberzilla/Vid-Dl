"""Core package initialization."""

from .download_manager import SOTADownloadManager
from .download_service import DownloadService
from .adapters import YtDlpBackend
from .controller import DownloadController
from .fallback import FallbackDownloader

__all__ = [
    "SOTADownloadManager",
    "DownloadService",
    "YtDlpBackend",
    "DownloadController",
    "FallbackDownloader",
]
