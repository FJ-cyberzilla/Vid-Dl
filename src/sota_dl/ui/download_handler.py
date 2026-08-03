from pathlib import Path
from typing import Any

from sota_dl.config.settings import COOKIES_PATH
from sota_dl.ui.colors import MUTED
from sota_dl.ui.banners import print_error, print_success, console
from sota_dl.ui.prompts import get_quality_choice
from sota_dl.core.event_bus import EventBus
from sota_dl.core.models import DownloadOptions, DownloadResult


# Factory to break circularity
def _get_downloader_factory() -> Any:
    from sota_dl.composition_root import create_sota_manager

    return create_sota_manager


def handle_results(results: list[DownloadResult], output_path: Path) -> None:
    """Display a summary of download results."""
    total = len(results)
    successful = sum(1 for r in results if r.status.value == "completed")
    failed = total - successful
    if successful == total:
        print_success(f"All {total} downloads completed successfully!")
    else:
        console.print(f"[yellow]{successful} succeeded, {failed} failed.[/]")
    console.print(f"Files saved to {output_path}")


def execute_download(choice: str, target: str, output_path: Path) -> None:
    """Execute download process."""
    is_audio = choice == "2"
    quality = get_quality_choice(is_audio)

    # Check for cookies file
    cookie_file = COOKIES_PATH if COOKIES_PATH.exists() else None

    download_options = DownloadOptions(
        quality=quality,
        format="mp3" if is_audio else None,
        output_dir=output_path,
        overwrite=False,
        retries=3,
        timeout=30.0,
        cookiefile=cookie_file,
    )

    event_bus = EventBus()
    create_manager = _get_downloader_factory()
    service = create_manager(event_bus=event_bus)

    try:
        console.print("\n")
        results = service.process_target(target, options=download_options)
        handle_results(results, output_path)
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
