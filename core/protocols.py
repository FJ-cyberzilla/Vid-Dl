"""Core protocols and interface definitions for the SOTA project."""

from typing import Protocol, Optional, Any


class ProgressReporter(Protocol):
    """Protocol for reporting download progress to a UI component."""

    def add_task(self, description: str, total: Optional[float] = None) -> int:
        """Initialize a new progress task."""
        ...

    def update(self, task_id: int, **kwargs: Any) -> None:
        """Update the state of an existing task."""
        ...

    def __enter__(self) -> "ProgressReporter":
        """Context manager support."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager support."""
        ...


class Downloader(Protocol):
    """Protocol for executing media downloads."""

    def execute(self, target: str) -> None:
        """Initiate the download process for a target URL or file."""
        ...
