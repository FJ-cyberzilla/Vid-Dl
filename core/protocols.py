"""Core protocols and interface definitions for the SOTA project."""

from typing import Protocol, Optional, Any, Dict
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


# ---------- Domain Models ----------
class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadOptions:
    """Configuration for a download operation."""
    output_dir: Path = Path(".")
    quality: str = "best"
    format: Optional[str] = None
    overwrite: bool = False
    retries: int = 3
    timeout: Optional[float] = 30.0
    cookiefile: Optional[Path] = None
    extra_args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DownloadResult:
    """Result of a download attempt."""
    status: DownloadStatus
    file_path: Optional[Path] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------- Progress Reporting ----------
TaskID = int

class ProgressReporter(Protocol):
    """
    Protocol for reporting progress to a UI component (e.g., Rich Progress).
    All methods are optional unless you need the full feature set.
    """

    def add_task(self, description: str, total: Optional[float] = None) -> TaskID:
        """Create a new progress task. Returns a unique task ID."""

    def update(
        self,
        task_id: TaskID,
        completed: Optional[float] = None,
        total: Optional[float] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        **extra: Any,
    ) -> None:
        """Update progress for an existing task."""

    def advance(self, task_id: TaskID, amount: float = 1.0) -> None:
        """Advance progress by a given amount."""

    def reset(self, task_id: TaskID, total: Optional[float] = None) -> None:
        """Reset task progress and optionally set a new total."""

    def remove_task(self, task_id: TaskID) -> None:
        """Remove a task from the progress display."""

    def set_description(self, task_id: TaskID, description: str) -> None:
        """Change the task's description."""

    def __enter__(self) -> "ProgressReporter":
        """Context manager entry."""

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""


# ---------- Download Execution ----------
class Downloader(Protocol):
    """
    Protocol for executing media downloads.
    Implementations should be reusable and stateless, or manage state internally.
    """

    def execute(self, target: str, options: DownloadOptions) -> DownloadResult:
        """
        Start a download and wait for completion.
        Returns a `DownloadResult` describing the outcome.
        """

    def cancel(self) -> None:
        """Cancel the currently running download (if any)."""

    def pause(self) -> None:
        """Pause the currently running download (if supported)."""

    def resume(self) -> None:
        """Resume a paused download (if supported)."""

    @property
    def status(self) -> DownloadStatus:
        """Current status of the ongoing download, or `PENDING` if none."""

    @property
    def progress_reporter(self) -> Optional[ProgressReporter]:
        """Get the current progress reporter, if any."""

    @progress_reporter.setter
    def progress_reporter(self, reporter: Optional[ProgressReporter]) -> None:
        """Attach a progress reporter to receive updates."""

    def __enter__(self) -> "Downloader":
        """Context manager entry – for resource setup."""

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit – for cleanup."""
