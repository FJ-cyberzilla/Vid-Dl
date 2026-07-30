"""Core package initialization."""

from .download_service import DownloadService
from .fallback import FallbackDownloader

__all__ = [
    "DownloadService",
    "FallbackDownloader",
]
