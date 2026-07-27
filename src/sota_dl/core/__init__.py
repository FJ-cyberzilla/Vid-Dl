"""Core package initialization."""

from .download_manager import SOTADownloadManager
from .download_service import DownloadService
from .controller import DownloadController
from .fallback import FallbackDownloader

__all__ = [
    "SOTADownloadManager",
    "DownloadService",
    "DownloadController",
    "FallbackDownloader",
]
