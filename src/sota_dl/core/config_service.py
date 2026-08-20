"""Service for managing application configuration state."""

from pathlib import Path
from sota_dl.core.protocols import ConfigurationProtocol
from sota_dl.infrastructure.adapters.browser_cookies import BrowserCookieAdapter


class ConfigurationService:
    """Service for managing application configuration state."""

    def __init__(self, settings: ConfigurationProtocol):
        self._settings = settings

    def extract_browser_cookies(self, browser: str = "chrome") -> tuple[bool, str]:
        """
        Extract cookies from browser databases.
        """
        try:
            with BrowserCookieAdapter() as adapter:
                # Assuming extracting for a dummy/general YouTube URL to populate cache
                # In a real scenario, this might need a specific domain or logic
                adapter.get_cookies_for_url("https://www.youtube.com", browser=browser)
                return True, "Browser cookies extracted successfully"
        except Exception as e:
            return False, f"Failed to extract browser cookies: {e}"

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
            self._settings.COOKIES_PATH = path
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
        if self._settings._is_writable(path):
            self._settings.ENV_OVERRIDE = path
            return True, f"Target updated: {path}"
        return False, f"Target not writable: {path}"

    def get_oauth_client_id(self) -> str:
        """Returns the OAuth client ID."""
        return self._settings.OAUTH_CLIENT_ID

    def get_oauth_client_secret(self) -> str:
        """Returns the OAuth client secret."""
        return self._settings.OAUTH_CLIENT_SECRET

    def store_oauth_tokens(self, access_token: str, refresh_token: str) -> None:
        """Stores the OAuth tokens securely."""
        # Implementation for secure storage
        self._settings.ACCESS_TOKEN = access_token
        self._settings.REFRESH_TOKEN = refresh_token

    def update_timeout(self, new_timeout: str) -> tuple[bool, str]:
        """Update the request timeout."""
        try:
            val = int(new_timeout)
            if val > 0:
                self._settings.TIMEOUT = val
                return True, f"Timeout updated to {val}s"
            return False, "Timeout must be > 0"
        except ValueError:
            return False, "Timeout must be a number"

    def toggle_debug(self) -> str:
        """Toggle debug mode."""
        self._settings.DEBUG = not self._settings.DEBUG
        return f"Debug mode: {'ON' if self._settings.DEBUG else 'OFF'}"
