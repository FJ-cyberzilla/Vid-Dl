"""Core orchestration service for managing download tasks."""

import os
import logging
import threading
from pathlib import Path
from typing import Any

from sota_dl.core.event_bus import EventBus
from sota_dl.core.protocols import (
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
    ProgressReporter,
    TaskID,
)
from sota_dl.core.fallback import FallbackDownloader

logger = logging.getLogger(__name__)


class DownloadService:
    """
    Orchestrates single or batch downloads, handling errors, progress,
    and state management (pause/cancel).
    """

    def __init__(
        self,
        downloader_backend: FallbackDownloader,
        default_options: DownloadOptions | None = None,
        progress_reporter: ProgressReporter | None = None,
        event_bus: EventBus | None = None,
    ):
        """
        Args:
            downloader_backend: Concrete backend implementation (e.g., YtDlpBackend).
            default_options: Fallback options if not overridden per target.
            progress_reporter: UI reporter for progress updates (optional).
            event_bus: Event bus for lifecycle management (optional).
        """
        self.downloader = downloader_backend
        self.default_options = default_options or DownloadOptions()
        self.progress_reporter = progress_reporter
        self.event_bus = event_bus

        # Internal state management
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancelled = False
        self._status: DownloadStatus = DownloadStatus.PENDING

        self._current_task_id: TaskID | None = None
        self._results: list[DownloadResult] = []

    def reset(self) -> None:
        self._cancelled = False
        self._pause_event.set()
        self._status = DownloadStatus.DOWNLOADING

    def cancel(self) -> None:
        self._cancelled = True
        self._pause_event.set()
        self._status = DownloadStatus.CANCELLED
        logger.info("Download cancellation requested.")

    def pause(self) -> None:
        self._pause_event.clear()
        self._status = DownloadStatus.PAUSED
        logger.info("Download paused.")

    def resume(self) -> None:
        self._pause_event.set()
        self._status = DownloadStatus.DOWNLOADING
        logger.info("Download resumed.")

    def _check_state(self) -> None:
        if not self._pause_event.is_set():
            self._pause_event.wait()
        if self._cancelled:
            raise Exception("Download cancelled by user")

    def process_target(
        self,
        target: str,
        options: DownloadOptions | None = None,
    ) -> list[DownloadResult]:
        """
        Process a target (single URL or batch file) and return results.
        """
        self.reset()
        self._results = []

        opts = options or self.default_options
        urls = self._resolve_targets(target)

        if self.progress_reporter:
            task_id = self.progress_reporter.add_task(
                description=f"Processing {len(urls)} downloads",
                total=len(urls),
            )
            self._current_task_id = task_id
        else:
            self._current_task_id = None

        self._execute_download_loop(urls, opts)

        if self.progress_reporter and self._current_task_id is not None:
            self.progress_reporter.update(
                self._current_task_id,
                completed=len(self._results),
                description=f"Completed {len(self._results)} downloads",
                status="done",
            )

        return self._results

    def _execute_download_loop(self, urls: list[str], opts: DownloadOptions) -> None:
        for idx, url in enumerate(urls, start=1):
            if self._cancelled:
                break
            self._check_state()

            logger.info("Downloading [%d/%d]: %s", idx, len(urls), url)

            # Using the backend directly for single download execution
            try:
                result = self.downloader.download(url, opts, self._progress_hook)
            except Exception as e:
                result = self._handle_download_error(url, e)

            self._results.append(result)
            self._update_loop_progress(idx, len(urls), url, result)

    def _progress_hook(self, d: dict[str, Any]) -> None:
        self._check_state()
        # Progress hooks are now handled here if needed,
        # or passed through to a specific backend
        pass

    def _update_loop_progress(
        self, idx: int, total: int, url: str, result: DownloadResult
    ) -> None:
        if self.progress_reporter and self._current_task_id is not None:
            self.progress_reporter.advance(self._current_task_id, amount=1.0)
            self.progress_reporter.update(
                self._current_task_id,
                description=f"Processed {idx}/{total} - last: {url}",
                status=result.status.value,
            )

    def _handle_download_error(self, url: str, error: Exception) -> DownloadResult:
        logger.exception("Error downloading %s", url)
        return DownloadResult(
            status=DownloadStatus.FAILED,
            error=str(error),
        )

    def _resolve_targets(self, target: str) -> list[str]:
        target = target.strip()
        if os.path.isfile(target) and target.lower().endswith((".txt", ".lst")):
            return self._parse_batch_file(target)
        return [target]

    def _parse_batch_file(self, file_path: str) -> list[str]:
        urls = []
        path = Path(file_path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
        if not urls:
            raise ValueError("Batch file contains no valid URLs.")
        return urls

    @property
    def results(self) -> list[DownloadResult]:
        return self._results.copy()
