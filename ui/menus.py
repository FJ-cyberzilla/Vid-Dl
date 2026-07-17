"""Interactive Command Center."""

import sys
from rich.prompt import Prompt
from config.settings import check_ffmpeg, get_download_path
from config.colors import THEME, MUTED
from ui.banners import render_main_banner, print_error, print_success, console
from core.download_manager import SOTADownloadManager
from core.download_service import DownloadService
from utils.validators import is_valid_input


def launch_command_center():
    """Main application loop."""
    if not check_ffmpeg():
        render_main_banner()
        print_error("FFmpeg is missing! In Termux, run: pkg install ffmpeg")
        sys.exit(1)

    while True:
        render_main_banner()
        console.print(f"[{MUTED}]Storage Route: {get_download_path()}[/]\n")

        console.print(f"[{THEME}]1.[/] Download Video (MP4 / Playlist / Batch)")
        console.print(f"[{THEME}]2.[/] Download Audio (MP3 / Playlist / Batch)")
        console.print(f"[{THEME}]3.[/] Exit System\n")

        choice = Prompt.ask(f"[{THEME}]Select Action[/]", choices=["1", "2", "3"])

        if choice == "3":
            console.print(f"\n[{MUTED}]Session terminated. Goodbye![/]")
            sys.exit(0)

        target = Prompt.ask(f"[{THEME}]Enter Media URL or /path/to/batch.txt[/]")
        if target:
            target = target.strip()

        if not target or not is_valid_input(target):
            print_error("Invalid input. Must be a valid URL or a local .txt file.")
            input("\nPress Enter to continue...")
            continue

        is_audio = choice == "2"

        console.print("\n")
        if is_audio:
            console.print(f"[{THEME}]1.[/] High (320kbps)")
            console.print(f"[{THEME}]2.[/] Medium (192kbps)")
            console.print(f"[{THEME}]3.[/] Low (128kbps)")
            q_choice = Prompt.ask(
                f"[{THEME}]Select Audio Quality[/]",
                choices=["1", "2", "3"],
                default="1",
            )
            quality_map = {"1": "320", "2": "192", "3": "128"}
        else:
            console.print(f"[{THEME}]1.[/] Maximum (1080p+)")
            console.print(f"[{THEME}]2.[/] High (720p)")
            console.print(f"[{THEME}]3.[/] Standard (480p)")
            q_choice = Prompt.ask(
                f"[{THEME}]Select Video Quality[/]",
                choices=["1", "2", "3"],
                default="1",
            )
            quality_map = {"1": "best", "2": "720", "3": "480"}

        selected_quality = quality_map[q_choice]
        manager = SOTADownloadManager(is_audio=is_audio, quality=selected_quality)
        service = DownloadService(manager)

        try:
            console.print("\n")
            service.process_target(target)
            print_success(f"Operation complete! Files saved to {get_download_path()}")
            input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            # Allows users to abort slow/mistaken downloads cleanly and return to menu
            console.print(f"\n[{MUTED}]Download cancelled by user. Returning to menu...[/]")
            input("\nPress Enter to continue...")
        except Exception as e:
            print_error(str(e))
            input("\nPress Enter to continue...")
