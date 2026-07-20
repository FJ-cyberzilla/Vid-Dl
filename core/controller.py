"""Controller for download lifecycle state."""
import threading
import logging
from typing import Optional
from core.protocols import ProgressReporter, TaskID, DownloadStatus

logger = logging.getLogger(__name__)

class DownloadController:
    """Manages cancellation, pause, and progress reporting."""
    
    def __init__(self, progress_reporter: Optional[ProgressReporter] = None):
        self.progress_reporter = progress_reporter
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancelled = False
        self.current_task_id: Optional[TaskID] = None
        self.status = DownloadStatus.PENDING
    
    def reset(self):
        self.cancelled = False
        self.pause_event.set()
        self.status = DownloadStatus.DOWNLOADING
        
    def cancel(self):
        self.cancelled = True
        self.pause_event.set()
        self.status = DownloadStatus.CANCELLED
    
    def pause(self):
        self.pause_event.clear()
        self.status = DownloadStatus.PAUSED
        
    def resume(self):
        self.pause_event.set()
        self.status = DownloadStatus.DOWNLOADING
        
    def check_state(self):
        if not self.pause_event.is_set():
            self.pause_event.wait()
            if self.cancelled:
                raise Exception("Download cancelled by user")
        if self.cancelled:
            raise Exception("Download cancelled by user")
