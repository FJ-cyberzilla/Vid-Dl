"""yt‑dlp integration – engine and protocol‑compliant adapter."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict, cast

import yt_dlp
from yt_dlp.utils import DownloadError

from sota_dl.core.models import DownloadOptions, DownloadResult, DownloadStatus

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


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------
class YtDlpError(Exception):
    """Raised when a yt‑dlp operation fails."""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class YtDlpEngine:
    """An enhanced wrapper around yt‑dlp."""

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

    def get_opts(
        self,
        extra_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build yt‑dlp options."""
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

    def download(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
    ) -> Path:
        """Download a single media resource."""
        self._validate_download_inputs(url, output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        path_container: dict[str, Path | None] = {"final_path": None}
        self._run_ydl(url, output_dir, progress_callback, extra_opts, path_container)

        return self._resolve_final_path(path_container)

    def _validate_download_inputs(self, url: str, output_dir: Path) -> None:
        """Validates inputs for the download method."""
        if not url or not output_dir:
            raise ValueError("Invalid URL or output directory")

    def _run_ydl(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Callable[[dict[str, Any]], Any] | None,
        extra_opts: dict[str, Any] | None,
        path_container: dict[str, Path | None],
    ) -> None:
        """Executes the yt-dlp download process."""

        def hook(d: ProgressDict) -> None:
            self._progress_hook(d, progress_callback, path_container)

        opts = self._build_ydl_opts(output_dir, extra_opts, hook)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except DownloadError as exc:
            self._handle_download_error(exc)

    def _resolve_final_path(self, path_container: dict[str, Path | None]) -> Path:
        """Resolves the final path from the path container."""
        final_path = path_container["final_path"]
        if final_path is None or not final_path.exists():
            raise YtDlpError(
                "Download finished but the output file could not be determined."
            )
        return final_path

    def _progress_hook(
        self,
        d: ProgressDict,
        callback: Callable[[dict[str, Any]], Any] | None,
        path_container: dict[str, Path | None],
    ) -> None:
        """Internal hook to track progress and final filename."""
        if d.get("status") == "finished" and "filename" in d:
            path_container["final_path"] = Path(d["filename"])
        if callback:
            callback(cast(dict[str, Any], d))

    def _handle_download_error(self, exc: DownloadError) -> None:
        """Handles yt-dlp download errors."""
        msg = str(exc).lower()
        if "members-only" in msg or "members on level" in msg:
            raise YtDlpError(
                "This is a members-only video. Please ensure you have a valid "
                "cookies.txt file configured in System Parameters."
            ) from exc
        raise YtDlpError(f"Download failed: {exc}") from exc

    def _build_ydl_opts(
        self,
        output_dir: Path,
        extra_opts: dict[str, Any] | None,
        hook: Callable[[ProgressDict], None],
    ) -> dict[str, Any]:
        """Helper to build yt-dlp options."""
        opts = self.get_opts(extra_opts)
        opts["outtmpl"] = str(output_dir / self.output_template)
        opts["progress_hooks"] = [hook]
        return opts

    async def download_async(
        self,
        url: str,
        output_dir: Path,
        *,
        progress_callback: Callable[[dict[str, Any]], Any] | None = None,
        extra_opts: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """Async wrapper around download."""
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


# ---------------------------------------------------------------------------
# Adapter (Protocol Compliant)
# ---------------------------------------------------------------------------
class YtDlpAdapter:
    """Adapter to map YtDlpEngine to DownloaderBackend protocol."""

    def __init__(self, engine: YtDlpEngine | None = None) -> None:
        self.engine = engine or YtDlpEngine()

    def download(
        self,
        target: str,
        options: DownloadOptions,
        progress_hook: Callable[[dict[str, Any]], Any],
    ) -> DownloadResult:
        """Execute a download."""
        extra_opts = options.extra_args.copy()
        if options.cookiefile:
            extra_opts["cookiefile"] = str(options.cookiefile)

        try:
            file_path = self.engine.download(
                target,
                options.output_dir,
                progress_callback=progress_hook,
                extra_opts=extra_opts,
            )
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                file_path=file_path,
                metadata={"target": target},
            )
        except YtDlpError as e:
            logger.exception("Download failed for %s", target)
            return DownloadResult(
                status=DownloadStatus.FAILED, error=str(e), metadata={"target": target}
            )
