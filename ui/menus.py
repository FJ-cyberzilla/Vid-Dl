"""Interactive Command Center."""

import sys
from pathlib import Path
from typing import Any
from collections.abc import Callable

from rich.prompt import Prompt

import config.settings
from config.colors import THEME, MUTED, ERROR
from config.settings import check_ffmpeg, get_download_path

from core.protocols import DownloadOptions, DownloadResult
from core.download_service import DownloadService
from utils.validators import is_valid_input
from ui.banners import render_main_banner, print_error, print_success, console
from ui.prompts import get_quality_choice
import ui.menu_renderer as menu_renderer


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
        menu_renderer.render_settings_menu(
            config.settings.COOKIES_PATH, config.settings.get_download_path()
        )

        choice = menu_renderer.get_menu_selection("Select Option", ["1", "2", "3", "4"])
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
    menu_renderer.render_dashboard(output_path)


def _handle_menu_selection() -> str:
    """Prompt the user for a menu selection."""
    return menu_renderer.get_menu_selection("Execute Command", ["1", "2", "3", "4"])


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
