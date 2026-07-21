"""Core protocols and interface definitions for the SOTA project."""

from typing import Protocol, Any
from collections.abc import Callable
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, Field


# ---------- Domain Models ----------
class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadOptions(BaseModel):
    """Configuration for a download operation with validation."""

    output_dir: Path = Field(default_factory=lambda: Path("."))
    quality: str = "best"
    format: str | None = None
    overwrite: bool = False
    retries: int = 3
    timeout: float | None = 30.0
    cookiefile: Path | None = None
    extra_args: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class DownloadResult(BaseModel):
    """Result of a download attempt with validation."""

    status: DownloadStatus
    file_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------- Progress Reporting ----------
TaskID = int


class ProgressReporter(Protocol):
    """
    Protocol for reporting progress to a UI component (e.g., Rich Progress).
    All methods are optional unless you need the full feature set.
    """

    def add_task(self, description: str, total: float | None = None) -> TaskID:
        """Create a new progress task. Returns a unique task ID."""

    def update(
        self,
        task_id: TaskID,
        completed: float | None = None,
        total: float | None = None,
        description: str | None = None,
        status: str | None = None,
        **extra: Any,
    ) -> None:
        """Update progress for an existing task."""

    def advance(self, task_id: TaskID, amount: float = 1.0) -> None:
        """Advance progress by a given amount."""

    def reset(self, task_id: TaskID, total: float | None = None) -> None:
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
class DownloaderBackend(Protocol):
    """
    Protocol for a download backend implementation.
    """

    def download(
        self, target: str, options: DownloadOptions, progress_hook: Callable
    ) -> DownloadResult:
        """Execute a download."""


class Downloader(Protocol):
    """
    Protocol for orchestrating media downloads.
    """

    def execute(self, target: str, options: DownloadOptions) -> DownloadResult:
        """
        Start a download and wait for completion.
        Returns a `DownloadResult` describing the outcome.
        """

    def cancel(self) -> None:
        """Cancel the currently running download."""

    def pause(self) -> None:
        """Pause the currently running download."""

    def resume(self) -> None:
        """Resume a paused download."""
