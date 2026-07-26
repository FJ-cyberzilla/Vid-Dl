"""Custom Rich Progress integrations."""

import sys
import logging
from typing import Any, cast
import contextlib

from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TaskID as RichTaskID,
)
from config.colors import THEME, ACCENT, MUTED
from core.protocols import ProgressReporter, TaskID

logger = logging.getLogger(__name__)

# Default refresh rate (adjust as needed)
DEFAULT_REFRESH_PER_SECOND = 10


class RichProgressReporter(ProgressReporter):
    """Wraps rich.progress.Progress to conform strictly to ProgressReporter Protocol."""

    def __init__(self, progress: Progress) -> None:
        self._progress = progress

    def add_task(self, description: str, total: float | None = None) -> TaskID:
        return int(self._progress.add_task(description, total=total))

    def update(
        self,
        task_id: TaskID,
        completed: float | None = None,
        total: float | None = None,
        description: str | None = None,
        status: str | None = None,
        **extra: Any,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if completed is not None:
            kwargs["completed"] = completed
        if total is not None:
            kwargs["total"] = total
        if description is not None:
            kwargs["description"] = description
        if status is not None:
            kwargs["status"] = status
        if extra:
            kwargs.update(extra)
        self._progress.update(RichTaskID(task_id), **kwargs)

    def advance(self, task_id: TaskID, amount: float = 1.0) -> None:
        self._progress.advance(RichTaskID(task_id), advance=amount)

    def reset(self, task_id: TaskID, total: float | None = None) -> None:
        self._progress.reset(RichTaskID(task_id), total=total)

    def remove_task(self, task_id: TaskID) -> None:
        self._progress.remove_task(RichTaskID(task_id))

    def set_description(self, task_id: TaskID, description: str) -> None:
        self._progress.update(RichTaskID(task_id), description=description)

    def __enter__(self) -> "RichProgressReporter":
        self._progress.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._progress.__exit__(exc_type, exc_val, exc_tb)


# Singleton holder using a mutable container to avoid 'global'
_PROGRESS_HOLDER: list[RichProgressReporter | None] = [
    None
]  # index 0 holds the singleton instance


def get_sota_progress() -> ProgressReporter:
    """
    Returns a persistent, richly styled Rich progress bar.

    The instance is created once and reused across all downloads to avoid
    spawning duplicate bars. It is auto‑disabled if stdout is not a TTY.

    Returns:
        A ProgressReporter instance (cached).
    """
    if _PROGRESS_HOLDER[0] is not None:
        return cast(ProgressReporter, _PROGRESS_HOLDER[0])

    # If not a TTY, create a disabled progress that still provides the API
    if not sys.stdout.isatty():
        logger.debug("Not a TTY – creating disabled progress bar.")
        progress = Progress(
            TextColumn("[dim]"),
            transient=True,
            refresh_per_second=0,
            disable=True,
        )
        reporter = RichProgressReporter(progress)
        _PROGRESS_HOLDER[0] = reporter
        return reporter

    # Full-featured progress bar – single instance
    logger.debug("Creating main SOTA progress bar.")
    progress = Progress(
        TextColumn(
            f"[{THEME}]Downloading [white]>[/] "
            f"[bold {ACCENT}][progress.description]%(task_description)s[/]"
        ),
        BarColumn(
            bar_width=35,
            complete_style=THEME,
            finished_style=ACCENT,
            pulse_style="white",
        ),
        DownloadColumn(),
        TextColumn(f"[{MUTED}]|[/]", justify="center"),
        TransferSpeedColumn(),
        TextColumn(f"[{MUTED}]|[/]", justify="center"),
        TimeRemainingColumn(),
        transient=False,  # Keep bars visible after completion
        refresh_per_second=DEFAULT_REFRESH_PER_SECOND,
    )
    reporter = RichProgressReporter(progress)
    _PROGRESS_HOLDER[0] = reporter
    return reporter


def reset_progress() -> None:
    """
    Reset the cached progress instance (useful for testing).
    After calling, the next get_sota_progress() will create a fresh one.
    """
    if _PROGRESS_HOLDER[0] is not None:
        # Optionally clean up the existing instance
        with contextlib.suppress(Exception):
            _PROGRESS_HOLDER[0].__exit__(None, None, None)
        _PROGRESS_HOLDER[0] = None
        logger.debug("Progress instance reset.")
