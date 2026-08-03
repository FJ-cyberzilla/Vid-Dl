"""Prompting utilities."""

import io
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from sota_dl.ui.colors import THEME, ACCENT, TEXT
from sota_dl.ui.banners import console


def get_audio_quality() -> str:
    """Prompt for audio quality."""
    table = Table(box=None, padding=(0, 1))
    table.add_column("Option", justify="right", style=ACCENT)
    table.add_column("Description", style=TEXT)
    table.add_row("1", "High-Fidelity Audio (320kbps)")
    table.add_row("2", "Standard Audio (192kbps)")
    table.add_row("3", "Compact Audio (128kbps)")

    console.print(
        Panel(
            table,
            title=f"[bold {THEME}]AUDIO ENGINE CONFIGURATION[/]",
            border_style=THEME,
            padding=(1, 2),
        )
    )
    q_choice = Prompt.ask(
        f"[{THEME}]Select Grade[/]",
        choices=["1", "2", "3"],
        default="1",
    )
    return {"1": "320", "2": "192", "3": "128"}[q_choice]


def get_video_quality() -> str:
    """Prompt for video quality."""
    table = Table(box=None, padding=(0, 1))
    table.add_column("Option", justify="right", style=ACCENT)
    table.add_column("Description", style=TEXT)
    table.add_row("1", "Ultra High Definition (1080p+)")
    table.add_row("2", "High Definition (720p)")
    table.add_row("3", "Standard Definition (480p)")

    console.print(
        Panel(
            table,
            title=f"[bold {THEME}]VIDEO STREAM CONFIGURATION[/]",
            border_style=THEME,
            padding=(1, 2),
        )
    )
    q_choice = Prompt.ask(
        f"[{THEME}]Select Grade[/]",
        choices=["1", "2", "3"],
        default="1",
    )
    return {"1": "best", "2": "720", "3": "480"}[q_choice]


def get_quality_choice(is_audio: bool) -> str:
    """
    Prompt the user for quality selection using a clean panel.
    """
    console.print("\n")
    return get_audio_quality() if is_audio else get_video_quality()


def show_qr_code(url: str) -> None:
    """
    Renders a QR code in the terminal.
    Gracefully falls back if qrcode library is not installed.
    Adapts layout for narrow terminals.
    """
    try:
        import qrcode  # type: ignore
    except ImportError:
        return

    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(url)
    qr.make(fit=True)

    # Inverted ASCII blocks for dark backgrounds
    f = io.StringIO()
    qr.print_ascii(out=f, invert=True)
    qr_str = f.getvalue()

    if console.width < 70:
        # Vertical layout for narrow screens
        console.print(f"[{TEXT}]Scan this QR code to continue:[/]")
        console.print(qr_str)
    else:
        # Standard layout
        console.print(
            Panel(
                qr_str,
                title=f"[bold {THEME}]AUTHORIZATION REQUIRED[/]",
                subtitle=f"[{TEXT}]Scan to authorize[/]",
                border_style=THEME,
                padding=(0, 2),
            )
        )
