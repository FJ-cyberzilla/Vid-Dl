"""Interactive Command Center."""

import sys
from pathlib import Path
from typing import Any
from collections.abc import Callable

from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

import config.settings
from config.colors import THEME, MUTED, ACCENT, TEXT, ERROR
from config.settings import check_ffmpeg, get_download_path
# Import specific classes to avoid circular imports if possible
# or re-order if necessary.
# The error suggests circularity between ui/menus <-> core/download_manager

from core.protocols import DownloadOptions, DownloadResult
from core.download_service import DownloadService
from utils.validators import is_valid_input
from ui.banners import render_main_banner, print_error, print_success, console
from ui.prompts import get_quality_choice


# Factory to break circularity
def _get_downloader_factory() -> Callable[..., Any]:
    from composition_root import create_sota_manager

    return create_sota_manager


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


def _update_cookies() -> None:
    """Handle cookies update."""
    new_path = Prompt.ask(f"[{THEME}]Enter path to cookies.txt[/]")
    if not new_path:
        return
    path = Path(new_path).expanduser().absolute()
    if path.exists():
        config.settings.COOKIES_PATH = path
        print_success(f"Source updated: {path}")
    else:
        print_error(f"Source not found: {path}")


def _update_download_path() -> None:
    """Handle download path update."""
    new_path = Prompt.ask(f"[{THEME}]Enter target directory[/]")
    if not new_path:
        return
    path = Path(new_path).expanduser().absolute()
    if config.settings._is_writable(path):
        config.settings.ENV_OVERRIDE = path
        print_success(f"Target updated: {path}")
    else:
        print_error(f"Target not writable: {path}")


def _handle_settings() -> None:
    """Handle the settings menu with a clean panel."""
    while True:
        settings_table = Table(box=None, show_header=False, padding=(0, 1))
        settings_table.add_column("ID", justify="right", style=ACCENT)
        settings_table.add_column("Option", style=TEXT)

        settings_table.add_row("1", "UPDATE COOKIES DATASOURCE")
        settings_table.add_row("2", "OVERRIDE DOWNLOAD PATH")
        settings_table.add_row("3", "AUTO-EXTRACT COOKIES (CHROME)")
        settings_table.add_row("4", "RETURN TO COMMAND CENTER")

        console.print(
            Panel(
                f"[dim]SOURCE:[/dim] {config.settings.COOKIES_PATH}\n"
                f"[dim]TARGET:[/dim] {config.settings.get_download_path()}\n\n",
                title=f"[bold {THEME}]SYSTEM CONFIGURATION[/]",
                border_style=THEME,
                padding=(1, 2),
            )
        )
        console.print(Panel(settings_table, border_style=MUTED, padding=(1, 2)))

        choice = Prompt.ask(f"[{THEME}]Select Option[/]", choices=["1", "2", "3", "4"])
        if choice == "1":
            _update_cookies()
        elif choice == "2":
            _update_download_path()
        elif choice == "3":
            from infrastructure.adapters.browser_cookies import BrowserCookieAdapter

            cookies = BrowserCookieAdapter.get_cookies_for_url(
                "youtube.com"
            )  # Extract cookies for target site
            if cookies:
                print_success("Successfully extracted cookies from Chrome")
            else:
                print_error("Failed to extract cookies")
        else:
            break


def _render_dashboard(output_path: Path) -> None:
    """Render the main menu dashboard."""
    render_main_banner()

    # Dashboard layout: Info and Menu in a structured grid
    dashboard = Table(box=None, expand=True, padding=(0, 0))
    dashboard.add_column(justify="center")

    # Display route information in a compact panel
    info_panel = Panel(
        f"[bold {ACCENT}]STORAGE :[/] [white]{output_path}[/]\n"
        f"[bold {ACCENT}]COOKIES :[/] [white]{config.settings.COOKIES_PATH}[/]",
        border_style=MUTED,
        padding=(0, 2),
        title=f"[bold {THEME}]SYSTEM STATUS[/]",
    )

    # Main Menu Table for better alignment
    menu_table = Table(box=None, show_header=False, padding=(0, 1))
    menu_table.add_column("ID", justify="right", style=ACCENT)
    menu_table.add_column("Command", style=f"bold {TEXT}")

    menu_table.add_row("1", "EXTRACT VIDEO STREAM (MP4/MKV)")
    menu_table.add_row("2", "EXTRACT AUDIO STREAM (MP3/M4A)")
    menu_table.add_row("3", "CONFIGURE SYSTEM PARAMETERS")
    menu_table.add_row("4", "TERMINATE SESSION")

    menu_panel = Panel(
        menu_table,
        title=f"[bold {THEME}]PRIMARY COMMANDS[/]",
        border_style=THEME,
        padding=(1, 2),
    )

    dashboard.add_row(info_panel)
    dashboard.add_row(menu_panel)

    console.print(dashboard)


def _handle_menu_selection() -> str:
    """Prompt the user for a menu selection."""
    return Prompt.ask(
        f"[{THEME}]Execute Command[/]",
        choices=["1", "2", "3", "4"],
    )


def _execute_download(choice: str, target: str, output_path: Path) -> None:
    """Execute download process."""
    is_audio = choice == "2"
    quality = get_quality_choice(is_audio)

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


def _process_exit() -> None:
    """Handle session termination."""
    console.print(f"\n[bold {ERROR}]Session terminated. Goodbye hacker![/]")
    sys.exit(0)


def _process_settings() -> None:
    """Handle settings menu."""
    _handle_settings()


def _process_download(choice: str, output_path: Path) -> None:
    """Handle media download process."""
    target = Prompt.ask(f"[{THEME}]Enter Media URL or /path/to/batch.txt[/]")
    target = target.strip() if target else ""

    if not target or not is_valid_input(target):
        print_error("Invalid input. Must be a valid URL or a local .txt file.")
        input("\nPress Enter to continue...")
        return

    _execute_download(choice, target, output_path)


def _process_command(choice: str, output_path: Path) -> None:
    """Process the selected command."""
    if choice == "4":
        _process_exit()
    elif choice == "3":
        _process_settings()
    else:
        _process_download(choice, output_path)


def launch_command_center() -> None:
    """Main application loop."""
    if not check_ffmpeg():
        render_main_banner()
        print_error("FFmpeg is missing! In Termux, run: pkg install ffmpeg")
        sys.exit(1)

    while True:
        output_path = Path(get_download_path())
        _render_dashboard(output_path)
        choice = _handle_menu_selection()
        _process_command(choice, output_path)


def main_menu() -> None:
    """Main menu entry point - launches the command center."""
    launch_command_center()
