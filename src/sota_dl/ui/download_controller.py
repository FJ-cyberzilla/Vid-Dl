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
    from sota_dl.container import create_sota_manager

    return create_sota_manager


def handle_results(results: list[DownloadResult], output_path: Path) -> None:
    """Display a summary of download results."""
    total = len(results)
    successful = _count_successful(results)
    
    _print_summary_badge(successful, total)
    console.print(f"Files saved to {output_path}")


def _count_successful(results: list[DownloadResult]) -> int:
    """Counts successful download results."""
    return sum(1 for r in results if r.status.value == "completed")


def _print_summary_badge(successful: int, total: int) -> None:
    """Prints a success or partial failure badge."""
    if successful == total:
        print_success(f"All {total} downloads completed successfully!")
        return

    failed = total - successful
    console.print(f"[yellow]{successful} succeeded, {failed} failed.[/]")


def execute_download(choice: str, target: str, output_path: Path) -> None:
    """Execute download process."""
    options = _prepare_options(choice, output_path)
    service = _get_downloader_factory()(event_bus=EventBus())

    try:
        _run_download_service(service, target, options, output_path)
    except KeyboardInterrupt:
        _handle_cancel(service)
    except (OSError, ValueError, AttributeError) as e:
        _handle_error(e)


def _prepare_options(choice: str, output_path: Path) -> DownloadOptions:
    """Prepares DownloadOptions based on user choice."""
    is_audio = choice == "2"
    return DownloadOptions(
        quality=get_quality_choice(is_audio),
        format="mp3" if is_audio else None,
        output_dir=output_path,
        overwrite=False,
        retries=3,
        timeout=30.0,
        cookiefile=COOKIES_PATH if COOKIES_PATH.exists() else None,
    )


def _run_download_service(
    service: Any, target: str, options: DownloadOptions, output_path: Path
) -> None:
    """Runs the download service and handles results."""
    console.print("\n")
    results = service.process_target(target, options=options)
    handle_results(results, output_path)
    input("\nPress Enter to continue...")


def _handle_cancel(service: Any) -> None:
    """Handles download cancellation."""
    service.cancel()
    console.print(f"\n[{MUTED}]Operation cancelled by user. Returning to menu...[/]")
    input("\nPress Enter to continue...")


def _handle_error(e: Exception) -> None:
    """Handles download errors."""
    print_error(str(e))
    input("\nPress Enter to continue...")
