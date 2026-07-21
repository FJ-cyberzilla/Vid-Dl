"""Core yt-dlp execution and configuration module."""

from pathlib import Path
import os
import logging

from config.colors import THEME
from ui.progress_bars import get_sota_progress
from core.protocols import (
    ProgressReporter,
    Downloader,
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
)
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
        downloader: FallbackDownloader,
        controller: DownloadController,
        default_options: DownloadOptions | None = None,
    ):
        """
        Args:
            downloader: FallbackDownloader instance.
            controller: DownloadController instance.
            default_options: Default download options.
        """
        self.default_options = default_options or DownloadOptions()
        # Dependency Injection
        self.downloader = downloader
        self.controller = controller
        self._last_result: DownloadResult | None = None

        self.default_options.output_dir.mkdir(parents=True, exist_ok=True)

    def execute(
        self, target: str, options: DownloadOptions | None = None
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
                    description=(
                        f"{'✔' if result.status == DownloadStatus.COMPLETED else '✘'} "
                        f"{target[:40]}"
                    ),
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
    def progress_reporter(self) -> ProgressReporter | None:
        return self.controller.progress_reporter

    @progress_reporter.setter
    def progress_reporter(self, reporter: ProgressReporter | None) -> None:
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
            clean_title = Path(filename).stem.rsplit(".", 1)[0][:40]

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
    def last_result(self) -> DownloadResult | None:
        return self._last_result
