"""UI Banners and static displays."""

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.colors import THEME, ACCENT, TEXT, ERROR, SUCCESS, MUTED
from utils.helpers import clear_screen

logger = logging.getLogger(__name__)

# ---- Configurable constants (centralise later) ----
__version__ = "3.0.1"
TAGLINE = "Zero-Cookie OAuth • Metadata • Dynamic Batches"

# Mutable container for the console instance (avolus 'global' statement)
_console_holder = [Console()]


def set_console(console: Console) -> None:
    """Replace the global console instance (useful for testing)."""
    _console_holder[0] = console


def _console() -> Console:
    """Return the current console instance."""
    return _console_holder[0]


def display_banner(clear: bool = True) -> None:
    """Alias for render_main_banner."""
    render_main_banner(clear)


def render_main_banner(clear: bool = True) -> None:
    """
    Render the top application banner with a professional, dashboard-style layout.

    Args:
        clear: If True (default), clear the screen before rendering.
    """
    if clear:
        clear_screen()

    console = _console()

    # Cybertronic ASCII Art
    ascii_banner = f"""[bold {THEME}]
   ____   ___  _____    __     ___  ____   ____  _     
  / ___| / _ \\|_   _|   \\ \\   / (_)|  _ \\ |  _ \\| |    
  \\___ \\| | | | | |      \\ \\ / /| || | | || | | | |    
   ___) | |_| | | |       \\ V / | || |_| || |_| | |___ 
  |____/ \\___/  |_|        \\_/  |_||____/ |____/|_____|
[/]"""

    # Create a table to center the banner
    table = Table(
        box=None,
        padding=(0, 0),
        expand=True,
    )
    table.add_column(justify="center")

    banner_text = (
        f"{ascii_banner}\n"
        f"[bold {TEXT}]SOTA [italic {ACCENT}]Media Extractor[/]\n"
        f"[dim]{TAGLINE}[/]"
    )

    panel = Panel(
        banner_text,
        border_style=THEME,
        title=f"[bold {ACCENT}] v{__version__} [/]",
        subtitle=f"[bold {THEME}]FJ™ Cybertronic Systems[/]",
        padding=(1, 2),
    )

    table.add_row(panel)
    console.print(table)


def print_error(msg: str) -> None:
    """
    Print an error message in red with an ✘ icon, and log it as an error.

    Args:
        msg: The error message to display.
    """
    logger.error(msg)
    _console().print(f"\n[{ERROR}]✘ ERROR:[/] {msg}")


def print_success(msg: str) -> None:
    """
    Print a success message in green with a ✔ icon, and log it as an info.

    Args:
        msg: The success message to display.
    """
    logger.info(msg)
    _console().print(f"\n[{SUCCESS}]✔ SUCCESS:[/] {msg}")


def print_troubleshooting(msg: str) -> None:
    """
    Print a troubleshooting tip in a muted color with a ⚙ icon.

    Args:
        msg: The troubleshooting message to display.
    """
    logger.info(f"Troubleshooting: {msg}")
    _console().print(f"\n[{MUTED}]⚙ TROUBLESHOOTING:[/] {msg}")


console = _console_holder[0]
