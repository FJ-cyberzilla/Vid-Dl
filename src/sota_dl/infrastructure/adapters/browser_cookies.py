"""
Infrastructure - Browser Cookie Adapter
Automates secure extraction of cookies from local browser profiles.
"""

import logging
import typing
from pathlib import Path
from sota_dl.infrastructure.app_dirs import DATA_DIR

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None

logger = logging.getLogger(__name__)


class BrowserCookieAdapter:
    """Provides utilities to extract cookies from various browsers."""

    @staticmethod
    def get_cookies_for_url(url: str, browser: str = "chrome") -> dict[str, str]:
        """
        Extracts cookies for a specific URL, trying dynamic extraction first,
        then falling back to a secure local file.

        Args:
            url: The URL to extract cookies for.
            browser: The browser name ('chrome', 'firefox', etc.).

        Returns:
            A dictionary of cookies.
        """
        cookies = BrowserCookieAdapter._try_dynamic_extraction(url, browser)
        if cookies:
            return cookies

        # 2. Fallback to secure local file
        cookie_file = DATA_DIR / "cookies.txt"
        if cookie_file.exists():
            logger.info("Loading cookies from %s", cookie_file)
            return BrowserCookieAdapter._load_cookies_from_file(cookie_file)

        return {}

    @staticmethod
    def _try_dynamic_extraction(url: str, browser: str) -> dict[str, str]:
        """Attempts to dynamically extract cookies from the specified browser."""
        if browser_cookie3 is None:
            logger.warning(
                "browser_cookie3 not installed; skipping dynamic extraction."
            )
            return {}

        try:
            cj = getattr(browser_cookie3, browser.lower())(domain_name=url)
            return {cookie.name: cookie.value for cookie in cj}
        except Exception as e:
            logger.warning("Dynamic cookie extraction failed: %s", e)
            return {}

    @staticmethod
    def _load_cookies_from_file(file_path: Path) -> dict[str, str]:
        """Loads Netscape-formatted cookies from a file."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return BrowserCookieAdapter._process_cookie_file(f)
        except Exception as e:
            logger.error("Failed to load cookies from %s: %s", file_path, e)
            return {}

    @staticmethod
    def _process_cookie_file(file_handle: typing.TextIO) -> dict[str, str]:
        """Parses a cookie file handle into a dictionary."""
        cookies = {}
        for line in file_handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                # Netscape format: domain, flag, path, secure,
                # expiration, name, value
                cookies[parts[5]] = parts[6].strip()
        return cookies
