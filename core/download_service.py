"""Orchestration service for managing download tasks."""

import os
import logging
import time
from typing import List, Optional

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
        default_options: Optional[DownloadOptions] = None,
        progress_reporter: Optional[ProgressReporter] = None,
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
        self._paused = False
        self._current_task_id: Optional[TaskID] = None
        self._results: List[DownloadResult] = []

        # Attach reporter to downloader if it supports it
        if hasattr(self.downloader, "progress_reporter"):
            self.downloader.progress_reporter = progress_reporter

    def process_target(
        self,
        target: str,
        options: Optional[DownloadOptions] = None,
    ) -> List[DownloadResult]:
        """
        Process a target (single URL or batch file) and return results for each URL.

        Args:
            target: URL or path to a .txt batch file.
            options: Override options for this run.

        Returns:
            List of DownloadResult for each processed URL.
        """
        self._cancelled = False
        self._paused = False
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

            while self._paused:
                # Busy‑wait or sleep; in a real app you'd use an event or condition
                time.sleep(0.1)
                if self._cancelled:
                    break

            logger.info("Downloading [%d/%d]: %s", idx, len(urls), url)
            try:
                result = self.downloader.execute(url, opts)
            except Exception as e:
                logger.exception("Unexpected error downloading %s", url)
                result = DownloadResult(
                    status=DownloadStatus.FAILED,
                    error=str(e),
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
        # Also cancel the underlying download if possible
        if hasattr(self.downloader, "cancel"):
            self.downloader.cancel()

    def pause(self) -> None:
        """Pause the current batch (after the current download finishes)."""
        self._paused = True

    def resume(self) -> None:
        """Resume a paused batch."""
        self._paused = False

    def _resolve_targets(self, target: str) -> List[str]:
        """Return a list of URLs from a single target or batch file."""
        target = target.strip()
        if os.path.isfile(target) and target.lower().endswith((".txt", ".lst")):
            return self._parse_batch_file(target)
        return [target]

    def _parse_batch_file(self, file_path: str) -> List[str]:
        """
        Parse a batch file, skipping empty lines and comments (#).
        """
        urls = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)

        if not urls:
            raise ValueError("Batch file contains no valid URLs.")
        return urls

    @property
    def results(self) -> List[DownloadResult]:
        """Return the results of the last batch."""
        return self._results.copy()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def is_paused(self) -> bool:
        return self._paused
