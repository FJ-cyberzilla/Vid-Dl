"""Cookie decryption and path resolution strategies."""

from pathlib import Path
import platform
import os
import structlog
from enum import Enum
from abc import ABC, abstractmethod
from typing import cast

logger = structlog.get_logger(__name__)


class DecryptionStrategy(ABC):
    @abstractmethod
    def decrypt(self, encrypted_value: bytes) -> str | None:
        pass


class DPAPIDecryptionStrategy(DecryptionStrategy):
    def decrypt(self, encrypted_value: bytes) -> str | None:
        try:
            import win32crypt

            data = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[
                1
            ]
            return cast(bytes, data).decode("utf-8")
        except ImportError:
            logger.error("win32crypt not available")
            return None
        except Exception as e:
            logger.error("Failed to decrypt with DPAPI", error=str(e))
            return None


class MacOSKeychainDecryptionStrategy(DecryptionStrategy):
    def decrypt(self, encrypted_value: bytes) -> str | None:
        # Implementation for macOS
        logger.warning("MacOSKeychainDecryptionStrategy not implemented")
        return None


class PassthroughDecryptionStrategy(DecryptionStrategy):
    def decrypt(self, encrypted_value: bytes) -> str | None:
        return encrypted_value.decode("utf-8", errors="ignore")


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    BRAVE = "brave"
    EDGE = "edge"
    OPERA = "opera"
    CHROME_MOBILE = "chrome_mobile"
    BRAVE_MOBILE = "brave_mobile"
    FIREFOX_MOBILE = "firefox_mobile"


class BrowserPathResolver:
    """Centralized configuration for browser profile paths."""

    def __init__(self) -> None:
        self.system = platform.system().lower()
        if self.system == "windows":
            self.system_key = "windows"
        elif self.system == "darwin":
            self.system_key = "darwin"
        else:
            self.system_key = "linux"

    def get_cookie_path(self, browser: BrowserType) -> Path | None:
        """Returns the default cookie path for the given browser and OS."""
        paths = self._get_browser_paths(browser)
        return paths.get(self.system_key)

    def _get_browser_paths(self, browser: BrowserType) -> dict[str, Path]:
        home = Path.home()

        # Simplified paths for demonstration, matching original BROWSER_CONFIGS
        if browser == BrowserType.CHROME:
            return {
                "linux": home
                / ".config"
                / "google-chrome"
                / "Default"
                / "Network"
                / "Cookies",
                "windows": Path(os.getenv("LOCALAPPDATA", ""))
                / "Google"
                / "Chrome"
                / "User Data"
                / "Default"
                / "Network"
                / "Cookies",
                "darwin": home
                / "Library"
                / "Application Support"
                / "Google"
                / "Chrome"
                / "Default"
                / "Cookies",
            }
        # ... add other browsers ...
        return {}
