"""Interactive Command Center."""

import sys
from pathlib import Path

from rich.prompt import Prompt

from config.colors import THEME, MUTED
from config.settings import check_ffmpeg, get_download_path
from core.download_manager import SOTADownloadManager
from core.download_service import DownloadService
from core.protocols import DownloadOptions
from utils.validators import is_valid_input  # moved before ui imports
from ui.banners import render_main_banner, print_error, print_success, console


def _get_quality_choice(is_audio: bool) -> str:
    """
    Prompt the user for quality selection and return the corresponding quality string.
    """
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
    return quality_map[q_choice]


def _handle_results(results, output_path: Path):
    """Display a summary of download results."""
    total = len(results)
    successful = sum(1 for r in results if r.status.value == "completed")
    failed = total - successful
    if successful == total:
        print_success(f"All {total} downloads completed successfully!")
    else:
        console.print(f"[yellow]{successful} succeeded, {failed} failed.[/]")
    console.print(f"Files saved to {output_path}")


def launch_command_center():
    """Main application loop."""
    if not check_ffmpeg():
        render_main_banner()
        print_error("FFmpeg is missing! In Termux, run: pkg install ffmpeg")
        sys.exit(1)

    while True:
        render_main_banner()
        output_path = Path(get_download_path())
        console.print(f"[{MUTED}]Storage Route: {output_path}[/]\n")

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
        quality = _get_quality_choice(is_audio)

        download_options = DownloadOptions(
            quality=quality,
            format="mp3" if is_audio else None,
            output_dir=output_path,
            overwrite=False,
            retries=3,
            timeout=30.0,
        )

        manager = SOTADownloadManager()
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

        except Exception as e:
            print_error(str(e))
            input("\nPress Enter to continue...")
