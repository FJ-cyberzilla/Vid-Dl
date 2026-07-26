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
    table = Table(box=None, padding=(0, 1))
    table.add_column("Option", justify="right", style=ACCENT)
    table.add_column("Description", style=TEXT)

    if is_audio:
        table.add_row("1", "High-Fidelity Audio (320kbps)")
        table.add_row("2", "Standard Audio (192kbps)")
        table.add_row("3", "Compact Audio (128kbps)")
        title = "AUDIO ENGINE CONFIGURATION"
        quality_map = {"1": "320", "2": "192", "3": "128"}
    else:
        table.add_row("1", "Ultra High Definition (1080p+)")
        table.add_row("2", "High Definition (720p)")
        table.add_row("3", "Standard Definition (480p)")
        title = "VIDEO STREAM CONFIGURATION"
        quality_map = {"1": "best", "2": "720", "3": "480"}

    console.print(
        Panel(
            table,
            title=f"[bold {THEME}]{title}[/]",
            border_style=THEME,
            padding=(1, 2),
        )
    )
    q_choice = Prompt.ask(
        f"[{THEME}]Select Grade[/]",
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
        settings_table = Table(box=None, show_header=False, padding=(0, 1))
        settings_table.add_column("ID", justify="right", style=ACCENT)
        settings_table.add_column("Option", style=TEXT)

        settings_table.add_row("1", "UPDATE COOKIES DATASOURCE")
        settings_table.add_row("2", "OVERRIDE DOWNLOAD PATH")
        settings_table.add_row("3", "RETURN TO COMMAND CENTER")

        console.print(
            Panel(
                f"[dim]SOURCE:[/dim] {config.settings.COOKIES_PATH}\n"
                f"[dim]TARGET:[/dim] {config.settings.get_download_path()}\n\n"
                + "[divider]\n" if hasattr(console, "divider") else "\n",
                title=f"[bold {THEME}]SYSTEM CONFIGURATION[/]",
                border_style=THEME,
                padding=(1, 2),
            )
        )
        console.print(
            Panel(
                settings_table,
                border_style=MUTED,
                padding=(1, 2),
            )
        )

        choice = Prompt.ask(f"[{THEME}]Select Option[/]", choices=["1", "2", "3"])
        if choice == "1":
            new_path = Prompt.ask(f"[{THEME}]Enter path to cookies.txt[/]")
            if new_path:
                path = Path(new_path).expanduser().absolute()
                if path.exists():
                    config.settings.COOKIES_PATH = path
                    print_success(f"Source updated: {path}")
                else:
                    print_error(f"Source not found: {path}")
        elif choice == "2":
            new_path = Prompt.ask(f"[{THEME}]Enter target directory[/]")
            if new_path:
                path = Path(new_path).expanduser().absolute()
                if config.settings._is_writable(path):
                    config.settings.ENV_OVERRIDE = path
                    print_success(f"Target updated: {path}")
                else:
                    print_error(f"Target not writable: {path}")
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

        choice = Prompt.ask(f"[{THEME}]Execute Command[/]", choices=["1", "2", "3", "4"])

        if choice == "4":
            console.print(f"\n[bold {ERROR}]Session terminated. Goodbye hacker![/]")
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
