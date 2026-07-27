"""Core yt-dlp execution and configuration module."""

from pathlib import Path
import os
import logging
from typing import Any

from sota_dl.config.colors import THEME
from sota_dl.ui.progress_bars import get_sota_progress
from sota_dl.core.protocols import (
    ProgressReporter,
    Downloader,
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
)
from sota_dl.core.controller import DownloadController
from sota_dl.core.fallback import FallbackDownloader
from sota_dl.core.event_bus import EventBus, ShutdownEvent

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
        event_bus: EventBus | None = None,
        default_options: DownloadOptions | None = None,
    ):
        """
        Args:
            downloader: FallbackDownloader instance.
            controller: DownloadController instance.
            event_bus: EventBus instance for lifecycle events.
            default_options: Default download options.
        """
        self.default_options = default_options or DownloadOptions()
        # Dependency Injection
        self.downloader = downloader
        self.controller = controller
        self.event_bus = event_bus
        self._last_result: DownloadResult | None = None

        if self.event_bus:
            self.event_bus.subscribe(ShutdownEvent, self._handle_shutdown)

        self.default_options.output_dir.mkdir(parents=True, exist_ok=True)

    async def _handle_shutdown(self, event: ShutdownEvent) -> None:
        """Handle application shutdown event."""
        logger.info("Shutdown event received. Cleaning up...")
        self.cancel()

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
            return self._handle_dry_run(target)

        with self.progress_reporter as progress:
            self.controller.current_task_id = progress.add_task(
                f"Preparing download: {target[:50]}...",
                total=None,
            )

            result = self.downloader.download(target, opts, self._progress_hook)

            self._finalize_progress(progress, result, target)

        self._last_result = result
        self.controller.status = result.status
        return result

    def _handle_dry_run(self, target: str) -> DownloadResult:
        logger.info("Dry run enabled: Skipping actual download for %s", target)
        return DownloadResult(
            status=DownloadStatus.COMPLETED,
            metadata={"target": target, "dry_run": True},
        )

    def _finalize_progress(
        self, progress: ProgressReporter, result: DownloadResult, target: str
    ) -> None:
        if self.controller.current_task_id is None:
            return

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
    def progress_reporter(self) -> ProgressReporter:
        return self.controller.progress_reporter or get_sota_progress()

    @progress_reporter.setter
    def progress_reporter(self, reporter: ProgressReporter | None) -> None:
        self.controller.progress_reporter = reporter or get_sota_progress()

    def __enter__(self) -> "SOTADownloadManager":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    # ---------- Internal Helpers ----------

    def _progress_hook(self, d: dict[str, Any]) -> None:
        """
        yt‑dlp progress hook that updates the Rich progress bar.
        """
        self.controller.check_state()

        if self.controller.current_task_id is None:
            return

        status = d.get("status")
        if status == "downloading":
            self._update_progress_from_dict(d)
        elif status == "finished":
            self._update_progress_finished()

    def _update_progress_from_dict(self, d: dict[str, Any]) -> None:
        """
        Updates the progress reporter based on the yt-dlp dictionary.
        """
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes", 0)
        filename = d.get("filename", "Media File")
        clean_title = Path(filename).stem.rsplit(".", 1)[0][:40]

        self.progress_reporter.update(
            self.controller.current_task_id,  # type: ignore[arg-type]
            description=f"[{THEME}]{clean_title}...",
            total=total if total > 0 else None,
            completed=downloaded,
            status="downloading",
        )

    def _update_progress_finished(self) -> None:
        """
        Updates the progress reporter when download is finished.
        """
        self.progress_reporter.update(
            self.controller.current_task_id,  # type: ignore[arg-type]
            description="[bold green]Processing metadata & merging...",
            status="processing",
        )

    @property
    def last_result(self) -> DownloadResult | None:
        return self._last_result
