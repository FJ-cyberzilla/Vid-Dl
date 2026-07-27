from pathlib import Path
from rich.prompt import Prompt
from sota_dl.config import settings
from sota_dl.config.colors import THEME
from sota_dl.ui.banners import print_error, print_success
import sota_dl.ui.menu_renderer as menu_renderer


def update_cookies() -> None:
    """Handle cookies update."""
    new_path = Prompt.ask(f"[{THEME}]Enter path to cookies.txt[/]")
    if not new_path:
        return
    path = Path(new_path).expanduser().absolute()
    if path.exists():
        settings.COOKIES_PATH = path
        print_success(f"Source updated: {path}")
    else:
        print_error(f"Source not found: {path}")


def update_download_path() -> None:
    """Handle download path update."""
    new_path = Prompt.ask(f"[{THEME}]Enter target directory[/]")
    if not new_path:
        return
    path = Path(new_path).expanduser().absolute()
    if settings._is_writable(path):
        settings.ENV_OVERRIDE = path
        print_success(f"Target updated: {path}")
    else:
        print_error(f"Target not writable: {path}")


def _handle_cookie_extraction() -> None:
    """Handle browser cookie extraction."""
    from sota_dl.infrastructure.adapters.browser_cookies import BrowserCookieAdapter

    cookies = BrowserCookieAdapter.get_cookies_for_url("youtube.com")
    if cookies:
        print_success("Successfully extracted cookies from Chrome")
    else:
        print_error("Failed to extract cookies")


def handle_settings() -> None:
    """Handle the settings menu with a clean panel."""
    handlers = {
        "1": update_cookies,
        "2": update_download_path,
        "3": _handle_cookie_extraction,
    }

    while True:
        menu_renderer.render_settings_menu(
            settings.COOKIES_PATH, settings.get_download_path()
        )

        choice = menu_renderer.get_menu_selection("Select Option", ["1", "2", "3", "4"])

        if choice in handlers:
            handlers[choice]()
        else:
            break
