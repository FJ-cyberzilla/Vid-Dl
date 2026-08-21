"""Interactive Command Center."""

import sys


from sota_dl.config.settings import check_ffmpeg
from sota_dl.infrastructure.providers.system_status_provider import SystemStatusProviderImpl
from sota_dl.ui.banners import render_main_banner, print_error
import sota_dl.ui.menu_renderer as menu_renderer

# ... (rest of the file content)

def launch_command_center() -> None:
    """Main application loop."""
    if not check_ffmpeg():
        render_main_banner()
        print_error("FFmpeg is missing! In Termux, run: pkg install ffmpeg")
        sys.exit(1)
        
    status_provider = SystemStatusProviderImpl()

    while True:
        status = status_provider.get_status()
        menu_renderer.render_dashboard(status)
        options = ["1", "2", "3", "4"]
        choice = menu_renderer.get_menu_selection("choose an option", options)
        _process_command(choice, status.local_storage_path)


def main_menu() -> None:
    """Main menu entry point - launches the command center."""
    launch_command_center()
