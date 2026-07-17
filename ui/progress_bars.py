"""Custom Rich Progress integrations."""

from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from config.colors import THEME, ACCENT, MUTED


def get_sota_progress() -> Progress:
    """Returns a highly customized, real-time Rich progress bar."""
    return Progress(
        TextColumn(
            f"[{THEME}]Downloading [white]>[/] [bold {ACCENT}][progress.description]%(task.description)s[/]"
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
        transient=True,
        refresh_per_second=10,
    )
