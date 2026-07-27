"""Controller for download lifecycle state."""

import threading
import logging
from sota_dl.core.protocols import ProgressReporter, TaskID, DownloadStatus

logger = logging.getLogger(__name__)


class DownloadController:
    """Manages cancellation, pause, and progress reporting."""

    def __init__(self, progress_reporter: ProgressReporter | None = None):
        self.progress_reporter = progress_reporter
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancelled = False
        self.current_task_id: TaskID | None = None
        self.status: DownloadStatus = DownloadStatus.PENDING

    def reset(self) -> None:
        self.cancelled = False
        self.pause_event.set()
        self.status = DownloadStatus.DOWNLOADING

    def cancel(self) -> None:
        self.cancelled = True
        self.pause_event.set()
        self.status = DownloadStatus.CANCELLED

    def pause(self) -> None:
        self.pause_event.clear()
        self.status = DownloadStatus.PAUSED

    def resume(self) -> None:
        self.pause_event.set()
        self.status = DownloadStatus.DOWNLOADING

    def check_state(self) -> None:
        if not self.pause_event.is_set():
            self.pause_event.wait()
            if self.cancelled:
                raise Exception("Download cancelled by user")
        if self.cancelled:
            raise Exception("Download cancelled by user")
