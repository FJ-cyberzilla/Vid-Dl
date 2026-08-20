from sota_dl.infrastructure.adapters.cookies.strategy import CookieExtractionStrategy
from sota_dl.infrastructure.adapters.cookies.netscape import NetscapeCookieStrategy
from sota_dl.infrastructure.errors import BrowserNotSupportedError

SUPPORTED_BROWSERS = {"chrome", "firefox", "brave", "netscape"}


def get_cookie_adapter(browser_name: str) -> None:
    normalized_name = browser_name.lower().strip()
    if normalized_name not in SUPPORTED_BROWSERS:
        raise BrowserNotSupportedError(browser_name)


class CookieExtractionFactory:
    """Factory to resolve and return the appropriate cookie extraction strategy."""

    @staticmethod
    def get_strategy(strategy_type: str) -> CookieExtractionStrategy:
        """Returns a concrete implementation of CookieExtractionStrategy."""
        if strategy_type == "netscape":
            return NetscapeCookieStrategy()

        raise ValueError(f"Unknown cookie extraction strategy: {strategy_type}")
