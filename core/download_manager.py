"""Core yt-dlp execution and configuration module."""

import os
import logging
import time
from typing import Optional
from pathlib import Path

import yt_dlp

from config.colors import THEME
from config.settings import COOKIES_PATH
from ui.progress_bars import get_sota_progress
from core.protocols import (
    ProgressReporter,
    Downloader,
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
    TaskID,
)

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download-related failures."""


class SOTADownloadManager(Downloader):
    """
    Production‑ready implementation of the Downloader protocol using yt-dlp.
    Supports audio/video, quality selection, cancellation, pause/resume,
    progress reporting, and structured results.
    """

    def __init__(
        self,
        default_options: Optional[DownloadOptions] = None,
        progress_reporter: Optional[ProgressReporter] = None,
    ):
        """
        Args:
            default_options: Default download options (overridden per execute call).
            progress_reporter: UI progress reporter (falls back to global instance).
        """
        self.default_options = default_options or DownloadOptions()
        self.progress_ui = progress_reporter or get_sota_progress()
        self._current_task_id: Optional[TaskID] = None
        self._status = DownloadStatus.PENDING
        self._cancelled = False
        self._paused = False
        self._last_result: Optional[DownloadResult] = None

        # Ensure output directory exists (using default options)
        os.makedirs(self.default_options.output_dir, exist_ok=True)

    # ---------- Downloader Protocol Implementation ----------

    def execute(
        self, target: str, options: Optional[DownloadOptions] = None
    ) -> DownloadResult:
        """
        Execute a download with the given target URL and options.
        Returns a DownloadResult describing the outcome.
        """
        opts = options or self.default_options
        self._cancelled = False
        self._paused = False
        self._status = DownloadStatus.DOWNLOADING
        self._last_result = None

        # Ensure output directory exists for this run
        os.makedirs(opts.output_dir, exist_ok=True)

        # Build yt-dlp configuration
        ydl_opts = self._build_ydl_opts(opts)

        with self.progress_ui as progress:
            self._current_task_id = progress.add_task(
                f"Preparing download: {target[:50]}...",
                total=None,
            )

            result = self._perform_download(target, ydl_opts, opts)

            # Finalise progress task
            progress.update(
                self._current_task_id,
                completed=100,
                description=f"{'✔' if result.status == DownloadStatus.COMPLETED else '✘'} {target[:40]}",
                status=result.status.value,
            )
            progress.remove_task(self._current_task_id)

        self._last_result = result
        self._status = result.status
        return result

    def _perform_download(self, target: str, ydl_opts: dict, opts: DownloadOptions) -> DownloadResult:
        """Helper to execute download, with fallback logic."""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target])
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                file_path=self._guess_output_path(target, opts),
                metadata={"target": target},
            )
        except yt_dlp.utils.DownloadError as e:
            if "Requested format is not available" in str(e):
                logger.warning("Format not available for %s. Retrying with 'best' format.", target)
                ydl_opts["format"] = "best"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([target])
                
                return DownloadResult(
                    status=DownloadStatus.COMPLETED,
                    file_path=self._guess_output_path(target, opts),
                    metadata={"target": target, "fallback": True},
                )
            
            logger.error("yt-dlp download error for %s: %s", target, str(e))
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error=str(e),
                metadata={"target": target},
            )
        except Exception as e:
            logger.exception("Unexpected error downloading %s", target)
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error=f"Unexpected error: {e}",
                metadata={"target": target},
            )

    def cancel(self) -> None:
        """Cancel the currently running download."""
        self._cancelled = True
        self._status = DownloadStatus.CANCELLED
        logger.info("Download cancellation requested.")

    def pause(self) -> None:
        """Pause the download (supported via progress hook sleep)."""
        self._paused = True
        self._status = DownloadStatus.PAUSED
        logger.info("Download paused.")

    def resume(self) -> None:
        """Resume a paused download."""
        self._paused = False
        self._status = DownloadStatus.DOWNLOADING
        logger.info("Download resumed.")

    @property
    def status(self) -> DownloadStatus:
        """Current download status."""
        return self._status

    @property
    def progress_reporter(self) -> Optional[ProgressReporter]:
        """Get the attached progress reporter."""
        return self.progress_ui

    @progress_reporter.setter
    def progress_reporter(self, reporter: Optional[ProgressReporter]) -> None:
        """Attach a progress reporter for UI updates."""
        self.progress_ui = reporter or get_sota_progress()

    def __enter__(self) -> "SOTADownloadManager":
        """Context manager entry – no special setup needed."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit – clean up resources if needed."""

    # ---------- Internal Helpers ----------

    def _build_ydl_opts(self, options: DownloadOptions) -> dict:
        """
        Construct yt‑dlp options dict from DownloadOptions, with progress hook.
        """
        is_audio = options.format in ("mp3", "m4a", "aac", "flac", "opus", "vorbis")
        quality = options.quality

        # Base options
        ydl_opts = {
            "outtmpl": str(options.output_dir / "%(title)s.%(ext)s"),
            "embedthumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "yes_playlist": True,
            "progress_hooks": [self._progress_hook],
            "retries": options.retries,
            "timeout": options.timeout or 30.0,
        }

        # Check for cookies file to prevent non-existent path warnings
        # Use provided cookiefile or fall back to COOKIES_PATH from settings
        cookie_source = options.cookiefile or COOKIES_PATH
        if cookie_source and os.path.exists(cookie_source) and os.path.getsize(cookie_source) > 0:
            ydl_opts["cookiefile"] = str(Path(cookie_source).absolute())
            logger.info("Using cookie file: %s", ydl_opts["cookiefile"])
        elif options.cookiefile:
             # If specifically requested but missing, we should probably warn
             logger.warning("Requested cookie file %s not found.", options.cookiefile)

        # Overwrite?
        if options.overwrite:
            ydl_opts["overwrites"] = True

        # Audio or video
        if is_audio:
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": options.format or "mp3",
                            "preferredquality": quality,
                        },
                        {"key": "FFmpegMetadata", "add_metadata": True},
                        {"key": "EmbedThumbnail"},
                    ],
                }
            )
        else:
            # Video – choose format based on quality string
            if quality == "best":
                video_format = "bestvideo+bestaudio/best"
            else:
                # Assume quality is a height, e.g., "720", "1080"
                video_format = f"bestvideo[height<={quality}]+bestaudio/best"
            ydl_opts.update(
                {
                    "format": video_format,
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {"key": "FFmpegMetadata", "add_metadata": True},
                        {"key": "EmbedThumbnail"},
                    ],
                }
            )

        # Merge any extra args from options (but don't override cookiefile)
        extra = options.extra_args.copy()
        # Ensure the original cookie logic takes precedence
        extra.pop("cookiefile", None)  # remove if present to avoid overriding
        ydl_opts.update(extra)

        return ydl_opts

    def _progress_hook(self, d: dict) -> None:
        """
        yt‑dlp progress hook that updates the Rich progress bar.
        Also checks cancellation and pause flags.
        """
        if self._current_task_id is None:
            return

        # Check cancellation – raise exception to stop download
        if self._cancelled:
            raise yt_dlp.utils.DownloadError("Download cancelled by user")

        # Check pause – sleep until resumed or cancelled
        if self._paused:
            while self._paused:
                time.sleep(0.1)
                if self._cancelled:
                    raise yt_dlp.utils.DownloadError("Download cancelled while paused")
            # After resuming, we continue

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            filename = d.get("filename", "Media File")
            clean_title = os.path.basename(filename).rsplit(".", 1)[0][:40]

            self.progress_ui.update(
                self._current_task_id,
                description=f"[{THEME}]{clean_title}...",
                total=total if total > 0 else None,
                completed=downloaded,
                status="downloading",
            )

        elif status == "finished":
            self.progress_ui.update(
                self._current_task_id,
                description="[bold green]Processing metadata & merging...",
                status="processing",
            )

    def _guess_output_path(
        self, target: str, options: DownloadOptions
    ) -> Optional[str]:
        """
        Try to guess the final file path. Best effort; not guaranteed.
        In a production implementation, you could capture the filename from the hook.
        """
        # Use target to make placeholder more informative
        safe_target = target.replace("/", "_").replace(":", "_")[:30]
        return str(options.output_dir / f"download_{safe_target}")

    # ---------- Additional API ----------
    @property
    def last_result(self) -> Optional[DownloadResult]:
        """The result of the last executed download."""
        return self._last_result
