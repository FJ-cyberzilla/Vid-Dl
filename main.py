"""Entry point for the SOTA Downloader."""

import sys
import logging
import argparse

from ui.menus import launch_command_center
from ui.banners import console, __version__  # grouped imports from ui
from config.colors import MUTED

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the SOTA Downloader."""
    parser = argparse.ArgumentParser(description="SOTA Media Extractor")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()  # we don't need any other args for now

    try:
        launch_command_center()
    except KeyboardInterrupt:
        console.print(f"\n[{MUTED}]Process interrupted by user. Exiting.[/]")
        sys.exit(130)  # standard exit code for SIGINT
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"\n[red]Fatal error: {e}[/]")
        console.print("Please check the log for details.")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
