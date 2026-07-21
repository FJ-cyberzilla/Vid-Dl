"""Orchestration service for managing download tasks."""

import os
import logging
import threading
from pathlib import Path

from core.protocols import (
    Downloader,
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
    ProgressReporter,
    TaskID,
)

logger = logging.getLogger(__name__)


class DownloadService:
    """
    Orchestrates single or batch downloads, handling errors, progress,
    cancellation, and configuration.
    """

    def __init__(
        self,
        downloader: Downloader,
        default_options: DownloadOptions | None = None,
        progress_reporter: ProgressReporter | None = None,
    ):
        """
        Args:
            downloader: Concrete downloader implementation.
            default_options: Fallback options if not overridden per target.
            progress_reporter: UI reporter for progress updates (optional).
        """
        self.downloader = downloader
        self.default_options = default_options or DownloadOptions()
        self.progress_reporter = progress_reporter
        self._cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Set means "not paused"
        self._current_task_id: TaskID | None = None
        self._results: list[DownloadResult] = []

        # Attach reporter to downloader if it supports it
        if hasattr(self.downloader, "progress_reporter"):
            self.downloader.progress_reporter = progress_reporter

    def process_target(
        self,
        target: str,
        options: DownloadOptions | None = None,
    ) -> list[DownloadResult]:
        """
        Process a target (single URL or batch file) and return results for each URL.

        Args:
            target: URL or path to a .txt batch file.
            options: Override options for this run.

        Returns:
            List of DownloadResult for each processed URL.
        """
        self._cancelled = False
        self._pause_event.set()
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

        for idx, url in enumerate(urls, start=1):
            if self._cancelled:
                logger.info("Batch cancelled by user.")
                break

            # Handle pause
            if not self._pause_event.is_set():
                self._pause_event.wait()
                if self._cancelled:
                    break

            logger.info("Downloading [%d/%d]: %s", idx, len(urls), url)
            try:
                result = self.downloader.execute(url, opts)
            except (ValueError, TypeError) as e:
                # Catch configuration or type errors
                logger.exception("Configuration error downloading %s", url)
                result = DownloadResult(
                    status=DownloadStatus.FAILED,
                    error=f"Config error: {e}",
                )
            except (OSError, KeyError, AttributeError) as e:
                # Catch unexpected system or parsing errors
                logger.exception("Unexpected system error downloading %s", url)
                result = DownloadResult(
                    status=DownloadStatus.FAILED,
                    error=f"Unexpected error: {e}",
                )

            self._results.append(result)

            # Update progress
            if self.progress_reporter and self._current_task_id is not None:
                self.progress_reporter.advance(self._current_task_id, amount=1.0)
                self.progress_reporter.update(
                    self._current_task_id,
                    description=f"Processed {idx}/{len(urls)} - last: {url}",
                    status=result.status.value,
                )

        # Final progress update
        if self.progress_reporter and self._current_task_id is not None:
            self.progress_reporter.update(
                self._current_task_id,
                completed=len(self._results),
                description=f"Completed {len(self._results)} downloads",
                status="done",
            )

        return self._results

    def cancel(self) -> None:
        """Cancel the current batch operation."""
        self._cancelled = True
        self._pause_event.set()  # Unpause to allow downstream cancellation
        # Also cancel the underlying download if possible
        if hasattr(self.downloader, "cancel"):
            self.downloader.cancel()

    def pause(self) -> None:
        """Pause the current batch (after the current download finishes)."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume a paused batch."""
        self._pause_event.set()

    def _resolve_targets(self, target: str) -> list[str]:
        """Return a list of URLs from a single target or batch file."""
        target = target.strip()
        if os.path.isfile(target) and target.lower().endswith((".txt", ".lst")):
            return self._parse_batch_file(target)
        return [target]

    def _parse_batch_file(self, file_path: str) -> list[str]:
        """
        Parse a batch file, skipping empty lines and comments (#).
        """
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
        """Return the results of the last batch."""
        return self._results.copy()
