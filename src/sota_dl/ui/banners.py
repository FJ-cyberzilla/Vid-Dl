"""UI Banners and static displays."""

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from sota_dl.ui.colors import THEME, ACCENT, TEXT, ERROR, SUCCESS, MUTED, WARNING
from sota_dl.utils.helpers import clear_screen

logger = logging.getLogger(__name__)

# ---- Configuration Constants ----
__version__ = "2.0.0"
TAGLINE = "Zero-Cookie OAuth • Metadata • Dynamic Batches"
APP_NAME = "SOTA Vid-Dl"
BRANDING = "FJ™ Cybertronic Systems"

# ASCII Art Banner using a new user-provided style
ASCII_BANNER = f"""
[bold {ACCENT}]
dP     dP oo       dP    888888ba  dP 
88     88          88    88    `8b 88 
88    .8P dP .d888b88    88     88 88 
88    d8' 88 88'  `88    88     88 88 
88  .d8P  88 88.  .88    88    .8P 88 
888888'   dP `88888P8    8888888P  dP 
oooooooooooooooooooooooooooooooooooooo
[/]"""

# ---- Console Management ----
_console_holder: list[Console] = [Console()]


def set_console(console: Console) -> None:
    """
    Replace the global console instance.

    Args:
        console: New Console instance to use.
    """
    _console_holder[0] = console


def get_console() -> Console:
    """
    Get the current console instance.

    Returns:
        The active Console instance.
    """
    return _console_holder[0]


def terminal_supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns:
        True if color is supported, False otherwise.
    """
    console = get_console()
    return console.color_system is not None


# ---- UI Rendering Functions ----
def render_main_banner(clear: bool = True) -> None:
    """
    Render the main application banner with professional dashboard layout.

    Args:
        clear: If True, clear the screen before rendering.
    """
    if clear:
        clear_screen()

    console = get_console()

    # Create centered table
    table = Table(box=None, padding=(0, 0), expand=True)
    table.add_column(justify="center")

    # Build banner content
    banner_text = f"{ASCII_BANNER}\n[bold {TEXT}]{APP_NAME}[/]\n[dim]{TAGLINE}[/]"

    # Create panel with branding
    panel = Panel(
        banner_text,
        border_style=THEME,
        title=f"[bold {ACCENT}] v{__version__} [/]",
        subtitle=f"[bold {THEME}]{BRANDING}[/]",
        padding=(1, 2),
    )

    table.add_row(panel)
    console.print(table)


def display_banner(clear: bool = True) -> None:
    """Alias for render_main_banner for backward compatibility."""
    render_main_banner(clear)


# ---- Message Functions ----
def print_error(msg: str, log: bool = True) -> None:
    """
    Print an error message with ✘ icon.

    Args:
        msg: The error message to display.
        log: If True, also log the message as an error.
    """
    if log:
        logger.error(msg)
    get_console().print(f"\n[{ERROR}]✘ ERROR:[/] {msg}")


def print_success(msg: str, log: bool = True) -> None:
    """
    Print a success message with ✔ icon.

    Args:
        msg: The success message to display.
        log: If True, also log the message as info.
    """
    if log:
        logger.info(msg)
    get_console().print(f"\n[{SUCCESS}]✔ SUCCESS:[/] {msg}")


def print_warning(msg: str, log: bool = True) -> None:
    """
    Print a warning message with ⚠ icon.

    Args:
        msg: The warning message to display.
        log: If True, also log the message as a warning.
    """
    if log:
        logger.warning(msg)
    get_console().print(f"\n[{WARNING}]⚠ WARNING:[/] {msg}")


def print_troubleshooting(msg: str, log: bool = True) -> None:
    """
    Print a troubleshooting tip with ⚙ icon.

    Args:
        msg: The troubleshooting message to display.
        log: If True, also log the message as info.
    """
    if log:
        logger.info(f"Troubleshooting: {msg}")
    get_console().print(f"\n[{MUTED}]⚙ TROUBLESHOOTING:[/] {msg}")


def print_info(msg: str, log: bool = True) -> None:
    """
    Print an informational message with ℹ icon.

    Args:
        msg: The info message to display.
        log: If True, also log the message as info.
    """
    if log:
        logger.info(msg)
    get_console().print(f"\n[{TEXT}]ℹ INFO:[/] {msg}")


# ---- Progress Indicators ----
def create_progress() -> Progress:
    """
    Create a progress bar with spinner for long-running operations.

    Returns:
        A configured Progress instance.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=get_console(),
    )


def show_spinner(message: str) -> None:
    """
    Display a spinner with a message.

    Args:
        message: The message to display with the spinner.
    """
    console = get_console()
    with console.status(f"[bold {ACCENT}]{message}...[/]", spinner="dots"):
        # Context manager handles the spinner
        pass  # This is just a display function


def clear_console() -> None:
    """Clear the console screen."""
    clear_screen()


# ---- Convenience Exports ----
console = get_console()

# Theme constants exported for external use
__all__ = [
    "set_console",
    "get_console",
    "display_banner",
    "render_main_banner",
    "print_error",
    "print_success",
    "print_warning",
    "print_troubleshooting",
    "print_info",
    "create_progress",
    "show_spinner",
    "clear_console",
    "terminal_supports_color",
    "APP_NAME",
    "BRANDING",
    "__version__",
]
