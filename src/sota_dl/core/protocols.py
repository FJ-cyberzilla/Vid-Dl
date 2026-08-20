"""Core protocols and interface definitions for the SOTA project."""

from typing import Protocol, Any
from pathlib import Path
from collections.abc import Callable
from typing import TypeAlias
from sota_dl.core.models import (
    DownloadOptions as DownloadOptions,
    DownloadResult as DownloadResult,
    DownloadStatus as DownloadStatus,
)  # noqa: F401

# ---------- Progress Reporting ----------
TaskID: TypeAlias = int


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

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""


# ---------- Download Execution ----------
class DownloaderBackend(Protocol):
    """
    Protocol for a download backend implementation.
    """

    def download(
        self,
        target: str,
        options: DownloadOptions,
        progress_hook: Callable[[dict[str, Any]], Any],
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


class MetadataCacheProtocol(Protocol):
    """Protocol for metadata cache implementation."""

    async def get(self, url_key: str) -> dict[str, Any] | None:
        """Retrieves cached metadata."""

    async def set(
        self, url_key: str, data: dict[str, Any], ttl: int | None = None
    ) -> None:
        """Stores cached metadata."""

    async def delete(self, url_key: str) -> bool:
        """Removes a cached entry."""

    async def clear(self) -> None:
        """Clears all cached entries."""


class ConfigurationProtocol(Protocol):
    """Protocol for application configuration."""

    COOKIES_PATH: Path
    ENV_OVERRIDE: Path | None
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    ACCESS_TOKEN: str | None
    REFRESH_TOKEN: str | None
    TIMEOUT: int
    DEBUG: bool

    def _is_writable(self, path: Path) -> bool: ...


class EventBusProtocol(Protocol):
    """Protocol for the event bus system."""

    async def publish(self, event: Any) -> None:
        """Publishes an event to all subscribers."""

    def subscribe(self, event_type: type, handler: Callable[[Any], Any]) -> None:
        """Subscribes a handler to an event type."""


class RepositoryProtocol(Protocol):
    """Protocol for persistence repositories."""

    def load_all(self) -> list[Any]:
        """Loads all items from the repository."""

    def save_item(self, item: Any) -> None:
        """Saves a single item to the repository."""
