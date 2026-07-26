"""Entry point for the SOTA Downloader."""

import sys
import argparse
import signal
import asyncio
from types import FrameType

from ui.menus import launch_command_center
from ui.banners import console, __version__
from config.colors import MUTED
from infrastructure.logger import setup_logger
from infrastructure.system_validator import verify_system_dependencies
from infrastructure.crash_reporter import report_crash
from core.event_bus import EventBus, ShutdownEvent
from composition_root import create_sota_manager

# Configure logging using infrastructure logger
logger = setup_logger("main")

# Global event bus for lifecycle management
event_bus = EventBus()


def _shutdown_handler(sig: int, frame: FrameType | None) -> None:
    """Handles SIGINT/SIGTERM for graceful shutdown."""
    console.print(
        f"\n[{MUTED}]Signal {sig} received. Performing graceful shutdown...[/]"
    )
    # Publish shutdown event
    asyncio.create_task(event_bus.publish(ShutdownEvent()))
    sys.exit(130)


async def async_main() -> None:
    """Main asynchronous entry point."""
    # Register signal handlers
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT, lambda: _shutdown_handler(signal.SIGINT, None)
    )
    loop.add_signal_handler(
        signal.SIGTERM, lambda: _shutdown_handler(signal.SIGTERM, None)
    )

    parser = argparse.ArgumentParser(description="SOTA Media Extractor")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()

    try:
        # Initialize manager with event bus
        create_sota_manager(event_bus=event_bus)
        launch_command_center()
    except Exception as e:
        crash_file = report_crash(e)
        logger.exception("Unexpected error")
        console.print(f"\n[red]Fatal error: {e}[/]")
        console.print(f"Please check the log: {crash_file}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
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
