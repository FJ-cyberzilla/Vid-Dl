"""UI Banners and static displays."""

import logging

from rich.console import Console
from rich.panel import Panel

from config.colors import THEME, ACCENT, TEXT, ERROR, SUCCESS
from utils.helpers import clear_screen

logger = logging.getLogger(__name__)

# ---- Configurable constants (centralise later) ----
__version__ = "1.0.0"
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
    Render the top application banner.

    Args:
        clear: If True (default), clear the screen before rendering.
    """
    if clear:
        clear_screen()

    console = _console()
    # Constrain panel width to avoid awkward wrapping
    width = min(console.width, 80) if console.width else 80

    banner_text = f"[{TEXT}]SOTA Media Extractor\n" f"[italic {ACCENT}]{TAGLINE}[/]"
    console.print(
        Panel(
            banner_text,
            border_style=THEME,
            title=f"[bold {THEME}]★ SOTA v{__version__} ★[/]",
            width=width,
        )
    )


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
console = _console_holder[0]
