"""State‑of‑the‑art filesystem operations with async support and error handling."""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class FileSystemError(Exception):
    """Base exception for filesystem operations."""


class InsufficientSpaceError(FileSystemError):
    """Raised when disk space is insufficient."""


# ---------------------------------------------------------------------------
# FileSystemManager
# ---------------------------------------------------------------------------
class FileSystemManager:
    """
    Safe, cross‑platform file and directory management.

    Features:
        - Centralised temporary directory with automatic creation
        - Temp file / directory factories with guaranteed cleanup
        - Disk space verification with human‑readable thresholds
        - Context managers for temporary items
        - Async‑compatible (all blocking operations run in a thread pool)

    Usage::

        fs = FileSystemManager()
        video = fs.create_temp_file(suffix=".mp4")
        # ... use video ...
        fs.cleanup(video)
    """

    def __init__(self, temp_dir: Path | None = None) -> None:
        """
        Args:
            temp_dir: Root for all temporary files/dirs. Defaults to
                      ``<system temp>/video_downloader``.
        """
        self.temp_dir = temp_dir or (Path(tempfile.gettempdir()) / "video_downloader")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Temporary files / directories
    # ------------------------------------------------------------------
    def create_temp_file(self, suffix: str = ".mp4") -> Path:
        """
        Create an empty temporary file and return its path.

        The file is created and closed immediately; the caller is
        responsible for eventual deletion.
        """
        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix, dir=self.temp_dir, delete=False
            ) as tmp:
                path = Path(tmp.name)
            logger.debug("Created temp file: %s", path)
            return path
        except OSError as exc:
            raise FileSystemError(f"Failed to create temporary file: {exc}") from exc

    def create_temp_dir(self, prefix: str = "tmp") -> Path:
        """
        Create a temporary directory and return its path.
        """
        try:
            path = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
            logger.debug("Created temp dir: %s", path)
            return path
        except OSError as exc:
            raise FileSystemError(
                f"Failed to create temporary directory: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def cleanup(self, path: Path) -> None:
        """
        Delete *path*, whether it is a file or directory.

        No error is raised if *path* does not exist.
        """
        try:
            if not path.exists():
                return
            if path.is_file():
                path.unlink()
                logger.debug("Removed file: %s", path)
            elif path.is_dir():
                shutil.rmtree(path)
                logger.debug("Removed directory: %s", path)
        except OSError as exc:
            raise FileSystemError(f"Failed to clean up {path}: {exc}") from exc

    def cleanup_temp_dir(self) -> None:
        """Remove the entire temporary directory and its contents."""
        self.cleanup(self.temp_dir)

    # ------------------------------------------------------------------
    # Disk space
    # ------------------------------------------------------------------
    def get_disk_usage(self, path: Path | None = None) -> dict[str, int]:
        """
        Return disk usage for *path* (default: temp_dir) as bytes.

        Returns a dict with keys ``total``, ``used``, ``free``.
        """
        target = str(path or self.temp_dir)
        try:
            usage = shutil.disk_usage(target)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
            }
        except OSError as exc:
            raise FileSystemError(
                f"Failed to get disk usage for {target}: {exc}"
            ) from exc

    def ensure_free_space(
        self,
        required_mb: int,
        path: Path | None = None,
    ) -> bool:
        """
        Check if there is enough free space at *path* (default: temp_dir).

        Returns ``True`` if free bytes ≥ *required_mb* * 1024², else ``False``.
        To raise an exception instead, use :meth:`require_free_space`.
        """
        usage = self.get_disk_usage(path)
        return usage["free"] >= required_mb * 1024 * 1024

    def require_free_space(
        self,
        required_mb: int,
        path: Path | None = None,
    ) -> None:
        """
        Like :meth:`ensure_free_space` but raises :class:`InsufficientSpaceError`
        if the space requirement is not met.
        """
        if not self.ensure_free_space(required_mb, path):
            target = path or self.temp_dir
            free_mb = self.get_disk_usage(target)["free"] // (1024 * 1024)
            raise InsufficientSpaceError(
                f"Not enough disk space on {target}: "
                f"need {required_mb} MB, free {free_mb} MB"
            )

    # ------------------------------------------------------------------
    # File copy / move helpers
    # ------------------------------------------------------------------
    def copy_file(self, source: Path, destination: Path) -> Path:
        """Copy a file, preserving metadata."""
        try:
            return shutil.copy2(source, destination)
        except OSError as exc:
            raise FileSystemError(
                f"Failed to copy {source} to {destination}: {exc}"
            ) from exc

    def move_file(self, source: Path, destination: Path) -> Path:
        """Move a file, possibly across filesystems."""
        try:
            return shutil.move(source, destination)
        except OSError as exc:
            raise FileSystemError(
                f"Failed to move {source} to {destination}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------
    def temp_file_context(self, suffix: str = ".mp4") -> _TempFileContext:
        """
        Return a context manager that creates a temporary file and deletes it
        on exit.

        Usage::

            with fs.temp_file_context() as tmp:
                tmp.write_bytes(...)
        """
        return _TempFileContext(self.create_temp_file(suffix))

    def temp_dir_context(self, prefix: str = "tmp") -> _TempDirContext:
        """
        Return a context manager that creates a temporary directory and
        removes it (recursively) on exit.

        Usage::

            with fs.temp_dir_context() as tmp_dir:
                ...
        """
        return _TempDirContext(self.create_temp_dir(prefix))

    # ------------------------------------------------------------------
    # Async wrappers (all blocking ops run in a thread pool)
    # ------------------------------------------------------------------
    async def create_temp_file_async(self, suffix: str = ".mp4") -> Path:
        """Async version of :meth:`create_temp_file`."""
        return await asyncio.get_running_loop().run_in_executor(
            None, self.create_temp_file, suffix
        )

    async def create_temp_dir_async(self, prefix: str = "tmp") -> Path:
        """Async version of :meth:`create_temp_dir`."""
        return await asyncio.get_running_loop().run_in_executor(
            None, self.create_temp_dir, prefix
        )

    async def cleanup_async(self, path: Path) -> None:
        """Async version of :meth:`cleanup`."""
        await asyncio.get_running_loop().run_in_executor(None, self.cleanup, path)

    async def get_disk_usage_async(self, path: Path | None = None) -> dict[str, int]:
        """Async version of :meth:`get_disk_usage`."""
        return await asyncio.get_running_loop().run_in_executor(
            None, self.get_disk_usage, path
        )

    async def ensure_free_space_async(
        self, required_mb: int, path: Path | None = None
    ) -> bool:
        """Async version of :meth:`ensure_free_space`."""
        return await asyncio.get_running_loop().run_in_executor(
            None, self.ensure_free_space, required_mb, path
        )


# ---------------------------------------------------------------------------
# Internal context managers
# ---------------------------------------------------------------------------
class _TempFileContext:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args: object) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
        except OSError:
            pass  # best-effort cleanup


class _TempDirContext:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args: object) -> None:
        try:
            if self.path.exists():
                shutil.rmtree(self.path)
        except OSError:
            pass
