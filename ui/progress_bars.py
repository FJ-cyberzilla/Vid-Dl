"""Custom Rich Progress integrations."""

import sys
import logging

from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from config.colors import THEME, ACCENT, MUTED
import contextlib

logger = logging.getLogger(__name__)

# Default refresh rate (adjust as needed)
DEFAULT_REFRESH_PER_SECOND = 10

# Singleton holder using a mutable container to avoid 'global'
_PROGRESS_HOLDER = [None]  # index 0 holds the singleton instance


def get_sota_progress() -> Progress:
    """
    Returns a persistent, richly styled Rich progress bar.

    The instance is created once and reused across all downloads to avoid
    spawning duplicate bars. It is auto‑disabled if stdout is not a TTY.

    Returns:
        A Progress instance (cached).
    """
    if _PROGRESS_HOLDER[0] is not None:
        return _PROGRESS_HOLDER[0]

    # If not a TTY, create a disabled progress that still provides the API
    if not sys.stdout.isatty():
        logger.debug("Not a TTY – creating disabled progress bar.")
        _PROGRESS_HOLDER[0] = Progress(
            TextColumn("[dim]"),
            transient=True,
            refresh_per_second=0,
            disable=True,
        )
        return _PROGRESS_HOLDER[0]

    # Full-featured progress bar – single instance
    logger.debug("Creating main SOTA progress bar.")
    _PROGRESS_HOLDER[0] = Progress(
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
    return _PROGRESS_HOLDER[0]


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
