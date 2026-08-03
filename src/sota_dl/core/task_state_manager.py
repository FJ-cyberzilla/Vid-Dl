"""Service for managing download task lifecycle state."""

import threading
import logging
from sota_dl.core.protocols import DownloadStatus

logger = logging.getLogger(__name__)


class TaskStateManager:
    """Manages pause/resume/cancel state for download tasks."""

    def __init__(self) -> None:
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancelled = False
        self._status: DownloadStatus = DownloadStatus.PENDING

    @property
    def status(self) -> DownloadStatus:
        return self._status

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def reset(self) -> None:
        self._cancelled = False
        self._pause_event.set()
        self._status = DownloadStatus.DOWNLOADING

    def cancel(self) -> None:
        self._cancelled = True
        self._pause_event.set()
        self._status = DownloadStatus.CANCELLED
        logger.info("Download cancellation requested.")

    def pause(self) -> None:
        self._pause_event.clear()
        self._status = DownloadStatus.PAUSED
        logger.info("Download paused.")

    def resume(self) -> None:
        self._pause_event.set()
        self._status = DownloadStatus.DOWNLOADING
        logger.info("Download resumed.")

    def check_state(self) -> None:
        """Blocks if paused, raises if cancelled."""
        if not self._pause_event.is_set():
            self._pause_event.wait()
        if self._cancelled:
            raise Exception("Download cancelled by user")
