from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TypedDict

class CookieMetadata(TypedDict):
    expires: datetime | None
    secure: bool
    domain: str
    path: str
    http_only: bool
    same_site: str | None


@dataclass
class CookieEntry:
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: datetime | None = None
    secure: bool = False
    http_only: bool = False
    same_site: str | None = None


@dataclass
class ExtractionResult:
    success: bool
    cookies: dict[str, str]
    metadata: dict[str, CookieMetadata] = field(default_factory=dict)
    source: str = ""
    error: str | None = None
    extraction_time_ms: float = 0.0


class CookieError(Exception):
    """Base exception for cookie-related errors."""
    pass


class CookieExtractionError(CookieError):
    """Failed to extract cookies."""

    def __init__(self, message: str, browser: str = "", domain: str = ""):
        self.browser = browser
        self.domain = domain
        super().__init__(f"Cookie extraction failed for {browser}/{domain}: {message}")


class CookieSecurityError(CookieError):
    """Security-related cookie errors."""
    pass


class CookieDatabaseLockedError(CookieError):
    """Browser database is locked (browser may be running)."""
    pass


class CookiePermissionError(CookieError):
    """Insufficient permissions to access browser data."""
    pass


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    BRAVE = "brave"
    EDGE = "edge"
    OPERA = "opera"
    CHROME_MOBILE = "chrome_mobile"
    BRAVE_MOBILE = "brave_mobile"
    FIREFOX_MOBILE = "firefox_mobile"


@dataclass
class BrowserConfig:
    """Configuration for a specific browser."""

    name: str
    paths: dict[str, Path]
    is_chromium_based: bool
    requires_encryption_handler: bool = True
    profile_detection_command: list[str] | None = None
