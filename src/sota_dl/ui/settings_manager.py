"""Settings management UI."""

from rich.panel import Panel
from rich.prompt import Prompt

from sota_dl.config import settings
from sota_dl.core.config_service import ConfigurationService
from sota_dl.infrastructure.adapters.cookies.factory import get_cookie_adapter
from sota_dl.infrastructure.errors import BrowserNotSupportedError
from sota_dl.ui.banners import console, print_error, print_success
from sota_dl.ui.colors import THEME
import sota_dl.ui.menu_renderer as menu_renderer

_config_service = ConfigurationService(settings)


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
    browser = Prompt.ask(
        f"[{THEME}]Enter browser name (chrome, firefox, brave, netscape)[/]"
    )
    try:
        get_cookie_adapter(browser)
        success, message = _config_service.extract_browser_cookies(browser)
        if success:
            print_success(message)
        else:
            print_error(message)
    except BrowserNotSupportedError as e:
        err_msg = f"[bold yellow]Browser '{e.browser_name}' not supported.[/bold yellow]\n\n"
        console.print(
            Panel(
                f"{err_msg}"
                "[white]Fallback options available:[/white]\n"
                "  • Provide [bold green]cookies.txt[/bold green]\n"
                "  • Use [bold green]OAuth login[/bold green]\n"
                "  • Continue [bold green]anonymously[/bold green]",
                title="[bold yellow]Browser Notice[/bold yellow]",
                border_style="yellow",
            )
        )


def update_timeout() -> None:
    """Handle timeout update."""
    new_timeout = Prompt.ask(f"[{THEME}]Enter new timeout (seconds)[/]")
    success, message = _config_service.update_timeout(new_timeout)
    if success:
        print_success(message)
    else:
        print_error(message)


def toggle_debug() -> None:
    """Toggle debug mode."""
    message = _config_service.toggle_debug()
    print_success(message)


def handle_settings() -> None:
    """Handle the settings menu with a clean panel."""
    handlers = {
        "1": update_cookies,
        "2": update_download_path,
        "3": _handle_cookie_extraction,
        "4": update_timeout,
        "5": toggle_debug,
    }

    while True:
        menu_renderer.render_settings_menu(
            settings.COOKIES_PATH,
            settings.get_download_path(),
            settings.TIMEOUT,
            settings.DEBUG,
        )

        choice = menu_renderer.get_menu_selection(
            "Select Option", ["1", "2", "3", "4", "5", "6"]
        )

        if choice in handlers:
            handlers[choice]()
        else:
            break
