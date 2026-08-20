"""Entry point for the SOTA Downloader."""

import argparse
import asyncio
import contextlib
import os
import signal
import sys
from types import FrameType

from rich.panel import Panel

from sota_dl.composition_root import create_sota_manager
from sota_dl.core.event_bus import EventBus, ShutdownEvent
from sota_dl.infrastructure.crash_reporter import report_crash
from sota_dl.infrastructure.logger import setup_logger
from sota_dl.infrastructure.system_validator import verify_system_dependencies
from sota_dl.ui.banners import __version__, console
from sota_dl.ui.colors import MUTED
from sota_dl.ui.menus import launch_command_center

# Configure logging using infrastructure logger
logger = setup_logger("main")

# Global event bus for lifecycle management
event_bus = EventBus()
shutdown_event = asyncio.Event()


def check_termux_full_install_guard() -> None:
    """Aborts execution if full extra dependencies are installed on Termux."""
    is_termux = "TERMUX_VERSION" in os.environ or sys.platform == "android"
    if is_termux:
        try:
            import cryptography  # noqa: F401

            console.print(
                Panel(
                    "[bold red]WARNING: Unsafe Full Installation![/bold red]\n\n"
                    "The '[full]' extra (specifically [bold]cryptography[/bold])\n"
                    "was installed on Termux. This causes Rust/C\n"
                    "compilation instabilities on Android systems.\n\n"
                    "[bold yellow]To fix this issue, run:[/bold yellow]\n"
                    "  [bold green]pip uninstall cryptography[/bold green]\n"
                    "  [bold green]pip install .[/bold green]",
                    title="[bold red]Termux Guard Alert[/bold red]",
                    border_style="red",
                )
            )
            sys.exit(1)
        except ImportError:
            pass


def print_success_branding() -> None:
    """Prints the branded success installation banner."""
    version_str = (
        f"[bold green]✓ Successfully running SOTA-Downloader "
        f"v{__version__}![/bold green]"
    )
    console.print(
        Panel(
            version_str,
            title="[bold green]SOTA-DOWNLOADER[/bold green]",
            subtitle="[green]Android/Termux Optimized[/green]",
            border_style="green",
        )
    )


def _shutdown_handler(sig: int, frame: FrameType | None) -> None:
    """Handles SIGINT/SIGTERM for graceful shutdown."""
    console.print(
        f"\n[{MUTED}]Signal {sig} received. Performing graceful shutdown...[/]"
    )
    loop = asyncio.get_running_loop()
    loop.call_soon_threadsafe(shutdown_event.set)


def _setup_signals(loop: asyncio.AbstractEventLoop) -> None:
    """Safely attach signal handlers on POSIX systems."""
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _shutdown_handler, sig, None)


async def _run_app_tasks() -> None:
    """Initializes and runs the core application tasks."""
    create_sota_manager(event_bus=event_bus)
    ui_task = asyncio.create_task(asyncio.to_thread(launch_command_center))

    _, pending = await asyncio.wait(
        [ui_task, shutdown_event.wait()],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if shutdown_event.is_set():
        console.print(f"\n[{MUTED}]Shutdown signal processed. Cleaning up...[/]")
        await event_bus.publish(ShutdownEvent())

    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def async_main() -> None:
    """Main asynchronous entry point."""
    _setup_signals(asyncio.get_running_loop())

    parser = argparse.ArgumentParser(description="SOTA Media Extractor")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()

    print_success_branding()

    try:
        await _run_app_tasks()
    except Exception as e:
        crash_file = report_crash(e)
        logger.exception("Unexpected error")
        console.print(f"\n[red]Fatal error: {e}[/]")
        console.print(f"Please check the log: {crash_file}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    # Check Termux guard constraints before startup
    check_termux_full_install_guard()

    # Perform pre-flight checks
    verify_system_dependencies()

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()


# Alias for console script compatibility
main_menu = main
