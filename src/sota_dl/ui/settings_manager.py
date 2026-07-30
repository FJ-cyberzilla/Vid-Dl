"""Settings management UI."""

from rich.prompt import Prompt
from sota_dl.config import settings
from sota_dl.ui.colors import THEME
from sota_dl.ui.banners import print_error, print_success
from sota_dl.core.config_service import ConfigurationService
import sota_dl.ui.menu_renderer as menu_renderer

_config_service = ConfigurationService()


def update_cookies() -> None:
    """Handle cookies update."""
    new_path = Prompt.ask(f"[{THEME}]Enter path to cookies.txt[/]")
    success, message = _config_service.update_cookies_path(new_path)
    if success:
        print_success(message)
    else:
        print_error(message)


def update_download_path() -> None:
    """Handle download path update."""
    new_path = Prompt.ask(f"[{THEME}]Enter target directory[/]")
    success, message = _config_service.update_download_path(new_path)
    if success:
        print_success(message)
    else:
        print_error(message)


def _handle_cookie_extraction() -> None:
    """Handle browser cookie extraction."""
    success, message = _config_service.extract_browser_cookies()
    if success:
        print_success(message)
    else:
        print_error(message)


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
