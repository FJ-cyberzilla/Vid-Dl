"""yt‑dlp integration wrapper – robust, async‑ready, with progress & error handling."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

import yt_dlp
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TypedDict for yt-dlp hooks
# ---------------------------------------------------------------------------
class ProgressDict(TypedDict, total=False):
    status: str
    filename: str
    total_bytes: int
    total_bytes_estimate: int
    downloaded_bytes: int
    # Add other fields as needed based on yt-dlp documentation


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------
class YtDlpError(Exception):
    """Raised when a yt‑dlp operation fails."""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class YtDlpEngine:
    """
    An enhanced wrapper around yt‑dlp.
    ...
    """

    def __init__(
        self,
        use_aria2c: bool = True,
        output_template: str = "%(title)s.%(ext)s",
        default_timeout: float | None = None,
    ) -> None:
        self.output_template = output_template
        self.default_timeout = default_timeout

        # Check for aria2c availability
        self._aria2c_available = shutil.which("aria2c") is not None
        if use_aria2c and not self._aria2c_available:
            logger.warning(
                "aria2c requested but not found; falling back to native downloader."
            )
        self.use_aria2c = use_aria2c and self._aria2c_available

    # ------------------------------------------------------------------
    # Options builder
    # ------------------------------------------------------------------
    def get_opts(
        self,
        extra_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build yt‑dlp options by merging sensible defaults with *extra_opts*.

        Parameters:
            extra_opts: Additional yt‑dlp options that override defaults.
        """
        opts: dict[str, Any] = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
        }
        if self.use_aria2c:
            opts.update(
                {
                    "external_downloader": "aria2c",
                    "external_downloader_args": ["-x", "16", "-k", "1M"],
                }
            )
        if extra_opts:
            opts.update(extra_opts)
        return opts

    # ------------------------------------------------------------------
    # Download (sync) – correct filename via progress hook
    # ------------------------------------------------------------------
    def download(
        self,
        url: str,
        output_dir: Path,
        *,
        progress_callback: Callable[[ProgressDict], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
    ) -> Path:
        """
        Download a single media resource.

        Parameters:
            url: The video URL (any site supported by yt‑dlp).
            output_dir: Directory where the file will be saved.
            progress_callback: Called with the yt‑dlp progress hook dictionary.
            extra_opts: Additional yt‑dlp options (merged with defaults).

        Returns:
            Path to the **final** output file (after post‑processing).

        Raises:
            YtDlpError: If the download fails for any reason.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        final_path: Path | None = None

        def _progress_hook(d: ProgressDict) -> None:
            nonlocal final_path
            # yt‑dlp passes a 'status' key: 'downloading', 'finished', etc.
            if d.get("status") == "finished" and "filename" in d:
                # The 'filename' field points to the final file after merging
                final_path = Path(d["filename"])
            if progress_callback:
                progress_callback(d)

        opts = self.get_opts(extra_opts)
        opts["outtmpl"] = str(output_dir / self.output_template)
        # Add our own progress hook *in addition* to any the caller might have
        # (the caller's callback is already invoked inside _progress_hook)
        opts["progress_hooks"] = [_progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])  # download returns 0 or 1 but we ignore it
        except DownloadError as exc:
            raise YtDlpError(f"Download failed: {exc}") from exc

        if final_path is None or not final_path.exists():
            raise YtDlpError(
                "Download finished but the output file could not be determined."
            )
        return final_path

    # ------------------------------------------------------------------
    # Async download
    # ------------------------------------------------------------------
    async def download_async(
        self,
        url: str,
        output_dir: Path,
        *,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """
        Async wrapper around :meth:`download`.

        Parameters:
            timeout: Override the default timeout. Uses :func:`asyncio.wait_for`.
        """
        loop = asyncio.get_running_loop()
        coro = loop.run_in_executor(
            None,
            self.download,
            url,
            output_dir,
            progress_callback,
            extra_opts,
        )
        if timeout is None:
            timeout = self.default_timeout
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro

    # ------------------------------------------------------------------
    # Playlist support (returns list of paths)
    # ------------------------------------------------------------------
    def download_playlist(
        self,
        url: str,
        output_dir: Path,
        *,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
    ) -> list[Path]:
        """
        Download a full playlist and return paths to all downloaded files.

        Returns:
            List of final file paths in the order they were downloaded.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        collected_paths: list[Path] = []

        def _progress_hook(d: dict[str, Any]) -> None:
            if d.get("status") == "finished" and "filename" in d:
                collected_paths.append(Path(d["filename"]))
            if progress_callback:
                progress_callback(d)

        opts = self.get_opts(extra_opts)
        opts["outtmpl"] = str(output_dir / self.output_template)
        opts["progress_hooks"] = [_progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except DownloadError as exc:
            raise YtDlpError(f"Playlist download failed: {exc}") from exc

        if not collected_paths:
            raise YtDlpError("Playlist download finished but no files were detected.")
        return collected_paths

    async def download_playlist_async(
        self,
        url: str,
        output_dir: Path,
        *,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> list[Path]:
        """Async wrapper around :meth:`download_playlist`."""
        loop = asyncio.get_running_loop()
        coro = loop.run_in_executor(
            None,
            self.download_playlist,
            url,
            output_dir,
            progress_callback,
            extra_opts,
        )
        if timeout is None:
            timeout = self.default_timeout
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro
