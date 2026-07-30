"""Core package initialization."""

from .download_service import DownloadService
from .fallback import FallbackDownloader
from sota_dl.infrastructure.errors import ExtractionError

__all__ = [
    "DownloadService",
    "FallbackDownloader",
    "ExtractionError",
]
