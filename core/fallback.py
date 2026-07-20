"""Composite downloader with fallback support."""
import logging
from typing import List, Callable
from core.protocols import DownloaderBackend, DownloadOptions, DownloadResult, DownloadStatus

logger = logging.getLogger(__name__)

class FallbackDownloader:
    """Tries multiple backends in sequence until one succeeds."""
    
    def __init__(self, backends: List[DownloaderBackend]):
        self.backends = backends
        
    def download(self, target: str, options: DownloadOptions, progress_hook: Callable) -> DownloadResult:
        last_error = None
        for backend in self.backends:
            try:
                logger.info("Attempting download with %s", backend.__class__.__name__)
                return backend.download(target, options, progress_hook)
            except Exception as e:
                logger.warning("Backend %s failed: %s", backend.__class__.__name__, e)
                last_error = e
                
        return DownloadResult(
            status=DownloadStatus.FAILED,
            error=f"All backends failed. Last error: {last_error}",
            metadata={"target": target},
        )
