"""Entry point for the SOTA Downloader."""

from ui.menus import launch_command_center
from ui.banners import console
from config.colors import MUTED


def main_menu():
    try:
        launch_command_center()
    except KeyboardInterrupt:
        console.print(f"\n[{MUTED}]Process interrupted by user. Exiting.[/]")


if __name__ == "__main__":
    main_menu()
