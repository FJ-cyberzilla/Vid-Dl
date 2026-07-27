"""
Infrastructure - Browser Cookie Adapter
Automates secure extraction of cookies from local browser profiles.
"""

import logging
from pathlib import Path
import browser_cookie3
from sota_dl.infrastructure.app_dirs import DATA_DIR

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
        # 1. Try dynamic extraction
        try:
            cj = getattr(browser_cookie3, browser.lower())(domain_name=url)
            cookies = {cookie.name: cookie.value for cookie in cj}
            if cookies:
                return cookies
        except Exception as e:
            logger.warning("Dynamic cookie extraction failed: %s", e)

        # 2. Fallback to secure local file
        cookie_file = DATA_DIR / "cookies.txt"
        if cookie_file.exists():
            logger.info("Loading cookies from %s", cookie_file)
            return BrowserCookieAdapter._load_cookies_from_file(cookie_file)

        return {}

    @staticmethod
    def _load_cookies_from_file(file_path: Path) -> dict[str, str]:
        """Loads Netscape-formatted cookies from a file."""
        cookies = {}
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip() or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        # Netscape format: domain, flag, path, secure,
                        # expiration, name, value
                        cookies[parts[5]] = parts[6].strip()
        except Exception as e:
            logger.error("Failed to load cookies from %s: %s", file_path, e)
        return cookies
