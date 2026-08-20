from pathlib import Path
import platform
import os
import structlog
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import cast, Any
from collections.abc import Mapping

logger = structlog.get_logger(__name__)

# ... (Previous BrowserType and BrowserPathResolver classes) ...


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


# ... (Previous classes) ...


class CookieValidator:
    """Utility to handle business logic of cookie validation."""

    @staticmethod
    def _is_expired(expires: object, now: datetime, domain: str | None) -> bool:
        """Checks if a cookie has expired."""
        if not isinstance(expires, datetime):
            return False
        
        if expires <= now:
            logger.debug("Cookie expired", domain=domain)
            return True
        return False

    @staticmethod
    def _domain_matches(cookie_domain: str, domain: str) -> bool:
        """Verifies if the cookie domain matches the target domain."""
        stripped = cookie_domain.lstrip(".")
        if not stripped or not domain:
            return True
            
        return any([
            stripped == domain,
            domain.endswith(f".{stripped}"),
            stripped.endswith(f".{domain}")
        ])

    @staticmethod
    def is_valid(
        cookie_meta: Mapping[str, Any], domain: str, now: datetime | None = None
    ) -> bool:
        """Validates a cookie against a domain and expiration."""
        if now is None:
            now = datetime.now(timezone.utc)

        cookie_domain = cast(str, cookie_meta.get("domain", ""))
        expires = cookie_meta.get("expires")

        if CookieValidator._is_expired(expires, now, cookie_domain):
            return False

        if not CookieValidator._domain_matches(cookie_domain, domain):
            logger.debug("Cookie domain mismatch", domain=cookie_domain, target=domain)
            return False
            
        return True


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
