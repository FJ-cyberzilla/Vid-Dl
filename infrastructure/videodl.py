"""State‑of‑the‑art HTTP fallback downloader with retries, progress, async support."""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import RequestException, Timeout as RequestsTimeout

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class DownloadError(Exception):
    """Base exception for download failures."""


class InvalidURLError(DownloadError):
    """The provided URL is invalid."""


class DownloadTimeoutError(DownloadError):
    """The download timed out."""


class FileWriteError(DownloadError):
    """Failed to write the downloaded data to disk."""


# ---------------------------------------------------------------------------
# Options container
# ---------------------------------------------------------------------------
@dataclass
class DownloadOptions:
    """Configuration for a single download operation.

    Attributes:
        progress_callback: Called as ``callback(downloaded_bytes, total_bytes)``.
            *total_bytes* is ``None`` if the server didn't send a Content‑Length.
        chunk_size: Number of bytes to read per chunk (default 8 KiB).
        timeout: Request timeout in seconds (overrides the downloader's default).
        retries: Number of retries on transient errors (default 3).
    """
    progress_callback: Callable[[int, int | None], Any] | None = None
    chunk_size: int = 8192       # 8 KiB
    timeout: float | None = None
    retries: int = 3


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------
class VideoDLFallback:
    """
    A robust, production‑ready downloader for simple HTTP(S) media files.

    Features:
        - Sync and async interfaces
        - Chunked download with real‑time progress
        - Automatic retries with exponential backoff
        - Configurable timeouts and chunk sizes
        - Comprehensive error handling

    Usage::

        dl = VideoDLFallback()
        path = dl.download("https://example.com/video.mp4", Path("./video.mp4"))
        # With progress:
        path = dl.download(url, out, DownloadOptions(
            progress_callback=lambda d, t: print(f"{d}/{t}")
        ))
        # Async:
        path = await dl.download_async(url, out)
    """

    BACKOFF_FACTOR = 1.5          # multiplier between retries

    def __init__(self, timeout: float = 30.0) -> None:
        """
        Args:
            timeout: Default connect & read timeout in seconds (passed to requests).
        """
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_url(url: str) -> None:
        """Raise InvalidURLError if *url* is not a plausible HTTP(S) URL."""
        if not isinstance(url, str) or not url.strip():
            raise InvalidURLError("URL must be a non‑empty string.")
        if not url.startswith(("http://", "https://")):
            raise InvalidURLError("URL must start with http:// or https://")

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        """Create the parent directory of *path* if it doesn't exist."""
        path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core download logic (sync)
    # ------------------------------------------------------------------
    def download(
        self,
        url: str,
        output_path: Path,
        options: DownloadOptions | None = None,
    ) -> Path:
        """
        Download a file from *url* to *output_path*.

        Parameters:
            url: The HTTP(S) URL of the file.
            output_path: Destination file path (parent dirs created automatically).
            options: Optional :class:`DownloadOptions` to configure progress,
                chunk size, timeout, and retries.

        Returns:
            The *output_path* where the file was saved.

        Raises:
            InvalidURLError: The URL is malformed.
            DownloadTimeoutError: The request timed out.
            DownloadError: Any other download failure.
            FileWriteError: The disk write failed.
        """
        if options is None:
            options = DownloadOptions()

        self._validate_url(url)
        self._ensure_dir(output_path)

        timeout = options.timeout if options.timeout is not None else self.timeout

        for attempt in range(1, options.retries + 1):
            try:
                return self._single_download(
                    url,
                    output_path,
                    progress_callback=options.progress_callback,
                    chunk_size=options.chunk_size,
                    timeout=timeout,
                )
            except (RequestException, DownloadTimeoutError) as exc:
                if attempt == options.retries:
                    logger.error("Download failed after %d attempts.", options.retries)
                    raise
                wait = self.BACKOFF_FACTOR ** (attempt - 1)
                logger.warning(
                    "Download attempt %d failed: %s. Retrying in %.1fs...",
                    attempt, exc, wait,
                )
                time.sleep(wait)

        # Unreachable
        raise DownloadError("Unexpected retry loop exit.")

    def _single_download(
        self,
        url: str,
        output_path: Path,
        *,
        progress_callback: Callable[[int, int | None], Any] | None,
        chunk_size: int,
        timeout: float,
    ) -> Path:
        """Perform a single download attempt (no retries)."""
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
        except RequestsTimeout as exc:
            raise DownloadTimeoutError(f"Request timed out: {url}") from exc
        except RequestException as exc:
            raise DownloadError(f"Request failed: {exc}") from exc

        total_size = response.headers.get("Content-Length")
        if total_size is not None:
            try:
                total_size_int = int(total_size)
            except ValueError:
                total_size_int = None
        else:
            total_size_int = None

        try:
            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter keep‑alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size_int)
        except OSError as exc:
            raise FileWriteError(
                f"Failed to write to {output_path}: {exc}"
            ) from exc

        return output_path

    # ------------------------------------------------------------------
    # Async download (runs sync in a thread)
    # ------------------------------------------------------------------
    async def download_async(
        self,
        url: str,
        output_path: Path,
        options: DownloadOptions | None = None,
    ) -> Path:
        """
        Async wrapper around :meth:`download`.

        Runs the blocking download in a thread pool, making it safe for
        use in asyncio applications without blocking the event loop.

        All parameters are the same as in :meth:`download`.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.download,
            url,
            output_path,
            options,
        )
