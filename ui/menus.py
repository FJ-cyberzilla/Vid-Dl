"""Interactive Command Center."""

import sys
from pathlib import Path
from typing import Any
from collections.abc import Callable

from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

import config.settings
from config.colors import THEME, MUTED, ACCENT
from config.settings import check_ffmpeg, get_download_path
# Import specific classes to avoid circular imports if possible
# or re-order if necessary.
# The error suggests circularity between ui/menus <-> core/download_manager

from core.protocols import DownloadOptions, DownloadResult
from core.download_service import DownloadService
from utils.validators import is_valid_input
from ui.banners import render_main_banner, print_error, print_success, console


# Factory to break circularity
def _get_downloader_factory() -> Callable[..., Any]:
    from composition_root import create_sota_manager

    return create_sota_manager


def _get_quality_choice(is_audio: bool) -> str:
    """
    Prompt the user for quality selection using a clean panel.
    """
    console.print("\n")
    if is_audio:
        options = (
            f"[{THEME}]1.[/] High (320kbps)\n"
            f"[{THEME}]2.[/] Medium (192kbps)\n"
            f"[{THEME}]3.[/] Low (128kbps)"
        )
        title = "Select Audio Quality"
        quality_map = {"1": "320", "2": "192", "3": "128"}
    else:
        options = (
            f"[{THEME}]1.[/] Maximum (1080p+)\n"
            f"[{THEME}]2.[/] High (720p)\n"
            f"[{THEME}]3.[/] Standard (480p)"
        )
        title = "Select Video Quality"
        quality_map = {"1": "best", "2": "720", "3": "480"}

    console.print(Panel(options, title=f"[bold]{title}[/]", border_style=THEME))
    q_choice = Prompt.ask(
        f"[{THEME}]Selection[/]",
        choices=["1", "2", "3"],
        default="1",
    )
    return quality_map[q_choice]


def _handle_results(results: list[DownloadResult], output_path: Path) -> None:
    """Display a summary of download results."""
    total = len(results)
    successful = sum(1 for r in results if r.status.value == "completed")
    failed = total - successful
    if successful == total:
        print_success(f"All {total} downloads completed successfully!")
    else:
        console.print(f"[yellow]{successful} succeeded, {failed} failed.[/]")
    console.print(f"Files saved to {output_path}")


def _handle_settings() -> None:
    """Handle the settings menu with a clean panel."""
    while True:
        console.print(
            Panel(
                f"[dim]Cookies Path:[/dim] {config.settings.COOKIES_PATH}\n"
                f"[dim]Download Path:[/dim] {config.settings.get_download_path()}\n\n"
                f"[{THEME}]1.[/] Update Cookies Path\n"
                f"[{THEME}]2.[/] Set Custom Download Path\n"
                f"[{THEME}]3.[/] Back to Main Menu",
                title="[bold]System Settings[/]",
                border_style=THEME,
            )
        )

        choice = Prompt.ask(f"[{THEME}]Select Option[/]", choices=["1", "2", "3"])
        if choice == "1":
            new_path = Prompt.ask(f"[{THEME}]Enter new cookies.txt path[/]")
            if new_path:
                path = Path(new_path).expanduser().absolute()
                if path.exists():
                    config.settings.COOKIES_PATH = path
                    print_success(f"Cookies path updated to: {path}")
                else:
                    print_error(f"File not found: {path}")
        elif choice == "2":
            new_path = Prompt.ask(f"[{THEME}]Enter custom download directory[/]")
            if new_path:
                path = Path(new_path).expanduser().absolute()
                if config.settings._is_writable(path):
                    config.settings.ENV_OVERRIDE = path
                    print_success(f"Download path updated to: {path}")
                else:
                    print_error(f"Path is not writable: {path}")
        else:
            break


def launch_command_center() -> None:
    """Main application loop."""
    if not check_ffmpeg():
        render_main_banner()
        print_error("FFmpeg is missing! In Termux, run: pkg install ffmpeg")
        sys.exit(1)

    while True:
        # ... inside launch_command_center ...
        render_main_banner()
        output_path = Path(get_download_path())

        # Dashboard layout: Info and Menu in a structured grid
        dashboard = Table(box=None, expand=True, padding=(0, 0))
        dashboard.add_column(justify="center")

        # Display route information in a compact panel
        info_panel = Panel(
            f"[dim]Storage:[/dim] {output_path}\n"
            f"[dim]Cookies:[/dim] {config.settings.COOKIES_PATH}",
            border_style=MUTED,
            padding=(0, 1),
            title="[bold]Session Info[/]",
        )

        # Main Menu Panel
        menu_items = (
            f"[{ACCENT}]1.[/] [bold]Download Video[/] (MP4/Playlist)\n"
            f"[{ACCENT}]2.[/] [bold]Download Audio[/] (MP3/Playlist)\n"
            f"[{ACCENT}]3.[/] System Settings\n"
            f"[{ACCENT}]4.[/] Exit System"
        )
        menu_panel = Panel(
            menu_items,
            title="[bold]Main Menu[/]",
            border_style=THEME,
            padding=(1, 2),
        )

        dashboard.add_row(info_panel)
        dashboard.add_row(menu_panel)

        console.print(dashboard)

        choice = Prompt.ask(f"[{THEME}]Select Action[/]", choices=["1", "2", "3", "4"])

        if choice == "4":
            console.print(f"\n[{MUTED}]Session terminated. Goodbye![/]")
            sys.exit(0)

        if choice == "3":
            _handle_settings()
            continue

        target = Prompt.ask(f"[{THEME}]Enter Media URL or /path/to/batch.txt[/]")
        if target:
            target = target.strip()

        if not target or not is_valid_input(target):
            print_error("Invalid input. Must be a valid URL or a local .txt file.")
            input("\nPress Enter to continue...")
            continue

        is_audio = choice == "2"
        quality = _get_quality_choice(is_audio)

        download_options = DownloadOptions(
            quality=quality,
            format="mp3" if is_audio else None,
            output_dir=output_path,
            overwrite=False,
            retries=3,
            timeout=30.0,
        )

        create_manager = _get_downloader_factory()
        manager = create_manager()
        service = DownloadService(manager)

        try:
            console.print("\n")
            results = service.process_target(target, options=download_options)
            _handle_results(results, output_path)
            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            service.cancel()
            console.print(
                f"\n[{MUTED}]Operation cancelled by user. Returning to menu...[/]"
            )
            input("\nPress Enter to continue...")

        except (OSError, ValueError, AttributeError) as e:
            print_error(str(e))
            input("\nPress Enter to continue...")


def main_menu() -> None:
    """Main menu entry point - launches the command center."""
    launch_command_center()
