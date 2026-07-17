"""UI Banners and static displays."""

from rich.console import Console
from rich.panel import Panel
from config.colors import THEME, ACCENT, TEXT, ERROR, SUCCESS
from utils.helpers import clear_screen

console = Console()


def render_main_banner():
    """Renders the top application banner."""
    clear_screen()
    tagline = "Zero-Cookie OAuth • Metadata • Dynamic Batches"
    banner_text = f"[{TEXT}]SOTA Media Extractor\n[italic {ACCENT}]{tagline}[/]"
    console.print(
        Panel(
            banner_text, border_style=THEME, title=f"[bold {THEME}]★ SOTA v1.0.0 ★[/]"
        )
    )


def print_error(msg: str):
    console.print(f"\n[{ERROR}]✘ ERROR:[/] {msg}")


def print_success(msg: str):
    console.print(f"\n[{SUCCESS}]✔ SUCCESS:[/] {msg}")
