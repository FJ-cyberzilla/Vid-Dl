"""Service for managing application configuration state."""

from pathlib import Path
from sota_dl.config import settings


class ConfigurationService:
    """Service for managing application configuration state."""

    def update_cookies_path(self, new_path: str) -> tuple[bool, str]:
        """
        Update the path to the cookies file.

        Args:
            new_path: The new path to the cookies file.

        Returns:
            A tuple of (success, message).
        """
        if not new_path:
            return False, "No path provided"

        path = Path(new_path).expanduser().absolute()
        if path.exists():
            settings.COOKIES_PATH = path
            return True, f"Source updated: {path}"
        return False, f"Source not found: {path}"

    def update_download_path(self, new_path: str) -> tuple[bool, str]:
        """
        Update the target download directory.

        Args:
            new_path: The new path to the download directory.

        Returns:
            A tuple of (success, message).
        """
        if not new_path:
            return False, "No path provided"

        path = Path(new_path).expanduser().absolute()
        if settings._is_writable(path):
            settings.ENV_OVERRIDE = path
            return True, f"Target updated: {path}"
        return False, f"Target not writable: {path}"

    def extract_browser_cookies(self) -> tuple[bool, str]:
        """
        Extract cookies from the browser.

        Returns:
            A tuple of (success, message).
        """
        from sota_dl.infrastructure.adapters.browser_cookies import BrowserCookieAdapter

        cookies = BrowserCookieAdapter.get_cookies_for_url("youtube.com")
        if cookies:
            return True, "Successfully extracted cookies from Chrome"
        return False, "Failed to extract cookies"
