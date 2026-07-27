"""
Infrastructure - Browser Cookie Adapter
Automates secure extraction of cookies from local browser profiles.
"""

import browser_cookie3
import logging

logger = logging.getLogger(__name__)


class BrowserCookieAdapter:
    """Provides utilities to extract cookies from various browsers."""

    @staticmethod
    def get_cookies_for_url(url: str, browser: str = "chrome") -> dict[str, str]:
        """
        Extracts cookies for a specific URL from the specified browser.

        Args:
            url: The URL to extract cookies for.
            browser: The browser name ('chrome', 'firefox', etc.).

        Returns:
            A dictionary of cookies.
        """
        try:
            cj = getattr(browser_cookie3, browser.lower())(domain_name=url)
            return {cookie.name: cookie.value for cookie in cj}
        except Exception as e:
            logger.error("Failed to extract cookies from %s: %s", browser, e)
            return {}
