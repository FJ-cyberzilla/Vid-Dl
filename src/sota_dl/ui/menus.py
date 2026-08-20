"""Interactive Command Center."""

import sys
from pathlib import Path

from rich.prompt import Prompt

from sota_dl.config.settings import check_ffmpeg, get_download_path
from sota_dl.ui.colors import ERROR, THEME
from sota_dl.support.validators import is_valid_input
from sota_dl.ui.banners import render_main_banner, print_error, console
import sota_dl.ui.menu_renderer as menu_renderer
import sota_dl.ui.settings_controller as settings_controller
import sota_dl.ui.download_controller as download_controller


def _process_exit() -> None:
    """Handle session termination."""
    console.print(f"\n[bold {ERROR}]System Logged Off.[/]")
    sys.exit(0)


def _process_download(choice: str, output_path: Path) -> None:
    """Handle media download process."""
    target = Prompt.ask(f"[{THEME}]Enter Media URL or /path/to/batch.txt[/]")
    target = target.strip() if target else ""

    if not target or not is_valid_input(target):
        print_error("Invalid input. Must be a valid URL or a local .txt file.")
        input("\nPress Enter to continue...")
        return

    download_controller.execute_download(choice, target, output_path)


def _process_command(choice: str, output_path: Path) -> None:
    """Process the selected command."""
    if choice == "4":
        _process_exit()
    elif choice == "3":
        settings_controller.handle_settings()
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
        menu_renderer.render_dashboard(output_path)
        options = ["1", "2", "3", "4"]
        choice = menu_renderer.get_menu_selection("choose an option", options)
        _process_command(choice, output_path)


def main_menu() -> None:
    """Main menu entry point - launches the command center."""
    launch_command_center()
