"""Core yt-dlp execution and configuration module."""

import os
import logging
from typing import Optional

from config.colors import THEME
from ui.progress_bars import get_sota_progress
from core.protocols import (
    ProgressReporter,
    Downloader,
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
)
from core.adapters import YtDlpBackend
from core.controller import DownloadController
from core.fallback import FallbackDownloader

logger = logging.getLogger(__name__)


class SOTADownloadManager(Downloader):
    """
    Production‑ready implementation of the Downloader protocol using composition.
    Delegates execution to a FallbackDownloader (containing YtDlpBackend)
    and lifecycle management to DownloadController.
    """

    def __init__(
        self,
        default_options: Optional[DownloadOptions] = None,
        progress_reporter: Optional[ProgressReporter] = None,
    ):
        """
        Args:
            default_options: Default download options.
            progress_reporter: UI progress reporter.
        """
        self.default_options = default_options or DownloadOptions()
        # Dependency Injection: FallbackDownloader with YtDlpBackend
        self.downloader = FallbackDownloader(backends=[YtDlpBackend()])
        self.controller = DownloadController(progress_reporter=progress_reporter or get_sota_progress())
        self._last_result: Optional[DownloadResult] = None

        os.makedirs(self.default_options.output_dir, exist_ok=True)

    def execute(
        self, target: str, options: Optional[DownloadOptions] = None
    ) -> DownloadResult:
        """
        Execute a download with the given target URL and options.
        """
        opts = options or self.default_options
        self.controller.reset()
        self._last_result = None

        if not opts.dry_run:
            os.makedirs(opts.output_dir, exist_ok=True)

        if opts.dry_run:
            logger.info("Dry run enabled: Skipping actual download for %s", target)
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                metadata={"target": target, "dry_run": True},
            )

        with self.controller.progress_reporter as progress:
            self.controller.current_task_id = progress.add_task(
                f"Preparing download: {target[:50]}...",
                total=None,
            )

            result = self.downloader.download(target, opts, self._progress_hook)

            # Finalise progress task
            if self.controller.current_task_id is not None:
                progress.update(
                    self.controller.current_task_id,
                    completed=100,
                    description=f"{'✔' if result.status == DownloadStatus.COMPLETED else '✘'} {target[:40]}",
                    status=result.status.value,
                )
                progress.remove_task(self.controller.current_task_id)

        self._last_result = result
        self.controller.status = result.status
        return result

    def cancel(self) -> None:
        self.controller.cancel()
        logger.info("Download cancellation requested.")

    def pause(self) -> None:
        self.controller.pause()
        logger.info("Download paused.")

    def resume(self) -> None:
        self.controller.resume()
        logger.info("Download resumed.")

    @property
    def status(self) -> DownloadStatus:
        return self.controller.status

    @property
    def progress_reporter(self) -> Optional[ProgressReporter]:
        return self.controller.progress_reporter

    @progress_reporter.setter
    def progress_reporter(self, reporter: Optional[ProgressReporter]) -> None:
        self.controller.progress_reporter = reporter or get_sota_progress()

    def __enter__(self) -> "SOTADownloadManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    # ---------- Internal Helpers ----------

    def _progress_hook(self, d: dict) -> None:
        """
        yt‑dlp progress hook that updates the Rich progress bar.
        """
        self.controller.check_state()
        
        if self.controller.current_task_id is None:
            return

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            filename = d.get("filename", "Media File")
            clean_title = os.path.basename(filename).rsplit(".", 1)[0][:40]

            self.controller.progress_reporter.update(
                self.controller.current_task_id,
                description=f"[{THEME}]{clean_title}...",
                total=total if total > 0 else None,
                completed=downloaded,
                status="downloading",
            )

        elif status == "finished":
            self.controller.progress_reporter.update(
                self.controller.current_task_id,
                description="[bold green]Processing metadata & merging...",
                status="processing",
            )

    @property
    def last_result(self) -> Optional[DownloadResult]:
        return self._last_result
