from typing import Protocol, TypeVar, Union
from pathlib import Path
from collections.abc import Callable
from typing import TypeAlias
from sota_dl.core.models import (
    DownloadOptions as DownloadOptions,
    DownloadResult as DownloadResult,
    DownloadStatus as DownloadStatus,
)
from sota_dl.core.models.system_status import SystemStatus

# Generic types for protocol definitions
T = TypeVar("T")

# ---------- Progress Reporting ----------
TaskID: TypeAlias = int

class ProgressReporter(Protocol):
    """
    Protocol for reporting progress to a UI component.
    """

    def add_task(self, description: str, total: float | None = None) -> TaskID:
        """Create a new progress task."""

    def update(
        self,
        task_id: TaskID,
        completed: float | None = None,
        total: float | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update progress for an existing task."""

    def advance(self, task_id: TaskID, amount: float = 1.0) -> None:
        """Advance progress by a given amount."""

    def reset(self, task_id: TaskID, total: float | None = None) -> None:
        """Reset task progress."""

    def remove_task(self, task_id: TaskID) -> None:
        """Remove a task."""

    def set_description(self, task_id: TaskID, description: str) -> None:
        """Change the task's description."""

    def __enter__(self) -> "ProgressReporter":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        """Context manager exit."""


# ---------- Download Execution ----------
class DownloaderBackend(Protocol):
    """Protocol for a download backend implementation."""

    def download(
        self,
        target: str,
        options: DownloadOptions,
        progress_hook: Callable[[dict[str, Union[str, float, int]]], None],
    ) -> DownloadResult:
        """Execute a download."""


class Downloader(Protocol):
    """Protocol for orchestrating media downloads."""

    def execute(self, target: str, options: DownloadOptions) -> DownloadResult:
        """Start a download and wait for completion."""

    def cancel(self) -> None:
        """Cancel the currently running download."""

    def pause(self) -> None:
        """Pause the currently running download."""

    def resume(self) -> None:
        """Resume a paused download."""


class MetadataCacheProtocol(Protocol):
    """Protocol for metadata cache implementation."""

    async def get(self, url_key: str) -> dict[str, str] | None:
        """Retrieves cached metadata."""

    async def set(
        self, url_key: str, data: dict[str, str], ttl: int | None = None
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

    async def publish(self, event: object) -> None:
        """Publishes an event."""

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        """Subscribes a handler."""


class RepositoryProtocol(Protocol):
    """Protocol for persistence repositories."""

    def load_all(self) -> list[object]:
        """Loads all items."""

    def save_item(self, item: object) -> None:
        """Saves a single item."""


class DRMService(Protocol):
    """Protocol for DRM decryption services."""

    async def adecrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """Download and decrypt a DRM‑protected video asynchronously."""


class SystemStatusProvider(Protocol):
    """Protocol for providing system status."""
    def get_status(self) -> SystemStatus:
        """Returns the current system status."""
