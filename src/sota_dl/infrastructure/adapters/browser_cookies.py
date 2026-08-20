"""
Infrastructure - Browser Cookie Adapter
Automates secure extraction of cookies from local browser profiles.
Supports Chrome, Firefox, Brave, Edge, Opera on desktop and mobile.
"""

from collections.abc import Callable, Iterator
from typing import Any, TypeVar, cast
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
import hashlib
import json
import logging
import os
import platform
import secrets
import shutil
import sqlite3
import configparser
import subprocess  # nosec
import tempfile
import threading
import time
from functools import wraps
from urllib.parse import urlparse
from dataclasses import dataclass
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey
import base64
from sota_dl.infrastructure.adapters.cookies.types import (
    CookieMetadata,
    ExtractionResult,
    CookieError,
    CookieExtractionError,
    CookieSecurityError,
    CookieDatabaseLockedError,
)
from sota_dl.infrastructure.adapters.cookies.factory import CookieExtractionFactory

T = TypeVar("T")

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None

logger = logging.getLogger(__name__)


# BrowserType and CookieMetadata/Entry/Result are now imported from .cookies.types


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    BRAVE = "brave"
    EDGE = "edge"
    OPERA = "opera"
    CHROME_MOBILE = "chrome_mobile"
    BRAVE_MOBILE = "brave_mobile"
    FIREFOX_MOBILE = "firefox_mobile"


class CookiePermissionError(CookieError):
    """Insufficient permissions to access browser data."""

    pass


@dataclass
class BrowserConfig:
    """Configuration for a specific browser."""

    name: str
    paths: dict[str, Path]
    is_chromium_based: bool
    requires_encryption_handler: bool = True
    profile_detection_command: list[str] | None = None


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying operations with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed "
                            f"for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed "
                            f"for {func.__name__}: {e}"
                        )

            if last_exception is not None:
                raise last_exception

            # This part should ideally not be reachable if exceptions exist
            raise RuntimeError("Unexpected end of retry loop")

        return wrapper

    return decorator


class BrowserCookieAdapter:
    """Cookie extraction adapter for major browsers."""

    BROWSER_CONFIGS = {
        BrowserType.CHROME: BrowserConfig(
            name="Chrome",
            paths={
                "linux": (
                    Path.home()
                    / ".config"
                    / "google-chrome"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "windows": (
                    Path(os.getenv("LOCALAPPDATA", ""))
                    / "Google"
                    / "Chrome"
                    / "User Data"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "darwin": (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Google"
                    / "Chrome"
                    / "Default"
                    / "Cookies"
                ),
            },
            is_chromium_based=True,
        ),
        BrowserType.BRAVE: BrowserConfig(
            name="Brave",
            paths={
                "linux": (
                    Path.home()
                    / ".config"
                    / "BraveSoftware"
                    / "Brave-Browser"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "windows": (
                    Path(os.getenv("LOCALAPPDATA", ""))
                    / "BraveSoftware"
                    / "Brave-Browser"
                    / "User Data"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "darwin": (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "BraveSoftware"
                    / "Brave-Browser"
                    / "Default"
                    / "Cookies"
                ),
            },
            is_chromium_based=True,
        ),
        BrowserType.EDGE: BrowserConfig(
            name="Edge",
            paths={
                "linux": (
                    Path.home()
                    / ".config"
                    / "microsoft-edge"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "windows": (
                    Path(os.getenv("LOCALAPPDATA", ""))
                    / "Microsoft"
                    / "Edge"
                    / "User Data"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "darwin": (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Microsoft Edge"
                    / "Default"
                    / "Cookies"
                ),
            },
            is_chromium_based=True,
        ),
        BrowserType.OPERA: BrowserConfig(
            name="Opera",
            paths={
                "linux": (
                    Path.home()
                    / ".config"
                    / "opera"
                    / "Default"
                    / "Network"
                    / "Cookies"
                ),
                "windows": (
                    Path(os.getenv("APPDATA", ""))
                    / "Opera Software"
                    / "Opera Stable"
                    / "Network"
                    / "Cookies"
                ),
                "darwin": (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "com.operasoftware.Opera"
                    / "Default"
                    / "Cookies"
                ),
            },
            is_chromium_based=True,
        ),
        BrowserType.FIREFOX: BrowserConfig(
            name="Firefox",
            paths={
                "linux": Path.home() / ".mozilla" / "firefox",
                "windows": (
                    Path(os.getenv("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
                ),
                "darwin": (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Firefox"
                    / "Profiles"
                ),
            },
            is_chromium_based=False,
        ),
    }

    def __init__(
        self,
        cookie_file: Path | None = None,
        use_encryption: bool = True,
        encryption_key: bytes | None = None,
        encryption_salt: bytes | None = None,
        validate_expiry: bool = True,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        connection_timeout: float = 5.0,
        temp_dir: Path | None = None,
    ):
        self.cookie_file = cookie_file or (Path.cwd() / "data" / "cookies.enc")
        self.use_encryption = use_encryption
        self.validate_expiry = validate_expiry
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = connection_timeout
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())

        self._metadata_lock = threading.RLock()
        self._file_lock = threading.RLock()

        self._cookie_metadata: dict[str, CookieMetadata] = {}
        self._metrics: dict[str, object] = {
            "extraction_attempts": 0,
            "extraction_successes": 0,
            "extraction_failures": 0,
            "last_extraction_time": None,
        }

        if self.use_encryption:
            self._setup_encryption(encryption_key, encryption_salt)

        self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"BrowserCookieAdapter initialized "
            f"(encryption={use_encryption}, browser retries={max_retries})"
        )

    def _setup_encryption(
        self, encryption_key: bytes | None = None, encryption_salt: bytes | None = None
    ) -> None:
        """Setup encryption with Fernet symmetric encryption."""
        try:
            key = self._resolve_encryption_key(encryption_key, encryption_salt)
            self.fernet = Fernet(key)
            logger.debug("Encryption setup completed successfully")

        except Exception as e:
            raise CookieSecurityError(f"Failed to setup encryption: {e}") from e

    def _resolve_encryption_key(
        self, encryption_key: bytes | None, encryption_salt: bytes | None
    ) -> bytes:
        """Resolves encryption key from arguments, env, or derivation."""
        if encryption_key:
            return self._normalize_key(encryption_key)

        env_key = os.getenv("COOKIE_ENCRYPTION_KEY")
        if env_key:
            return env_key.encode()

        return self._derive_key(encryption_salt)

    def _normalize_key(self, key: bytes) -> bytes:
        if len(key) != 44:
            return base64.urlsafe_b64encode(key[:32])
        return key

    def _derive_key(self, salt: bytes | None) -> bytes:
        """Derives a secure encryption key."""
        if salt is None:
            salt = self._get_or_create_salt()

        machine_id = self._get_machine_id()
        key_material = f"{machine_id}{platform.node()}{os.getpid()}".encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(key_material))

    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create a new one securely."""
        salt_file = self.cookie_file.parent / ".cookie_salt"

        try:
            if salt_file.exists():
                return salt_file.read_bytes()

            salt = secrets.token_bytes(16)
            salt_file.write_bytes(salt)
            os.chmod(salt_file, 0o600)

            return salt

        except Exception as e:
            logger.warning(f"Could not persist salt, using ephemeral: {e}")
            return secrets.token_bytes(16)

    def _get_machine_id(self) -> str:
        """Get a unique machine identifier."""
        try:
            return self._calculate_machine_id()
        except Exception:
            return hashlib.sha256(platform.node().encode()).hexdigest()

    def _calculate_machine_id(self) -> str:
        """Determines machine id based on OS."""
        if platform.system() == "Linux":
            return self._get_linux_machine_id()
        if platform.system() == "Darwin":
            return self._get_darwin_machine_id()
        return hashlib.sha256(platform.node().encode()).hexdigest()

    def _get_linux_machine_id(self) -> str:
        machine_id = Path("/etc/machine-id").read_text().strip()
        return hashlib.sha256(machine_id.encode()).hexdigest()

    def _get_darwin_machine_id(self) -> str:
        result = subprocess.run(  # nosec
            ["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            text=True,
        )
        machine_id = platform.node()
        for line in result.stdout.split("\n"):
            if "IOPlatformUUID" in line:
                machine_id = line.split('"')[-2]
                break
        return hashlib.sha256(machine_id.encode()).hexdigest()

    @contextmanager
    def _sqlite_connection(
        self, db_path: Path, timeout: float | None = None
    ) -> Iterator[sqlite3.Connection]:
        """Context manager for SQLite connections with simplified error handling."""
        timeout = timeout or self.connection_timeout
        conn = None
        try:
            conn = sqlite3.connect(
                str(db_path), timeout=timeout, isolation_level="IMMEDIATE"
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            yield conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                raise CookieDatabaseLockedError(f"DB locked: {db_path}") from e
            raise CookieExtractionError(f"DB error: {e}") from e
        finally:
            if conn:
                conn.close()

    @contextmanager
    def _temp_file_copy(self, source: Path) -> Iterator[Path]:
        """Create a temporary copy of a file."""
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        if not os.access(source, os.R_OK):
            raise CookiePermissionError(f"No read permission for {source}")

        with tempfile.NamedTemporaryFile(
            dir=self.temp_dir,
            prefix=f"cookie_extract_{source.stem}_",
            suffix=source.suffix,
            delete=False,
        ) as temp_file:
            shutil.copy2(source, temp_file.name)
            os.chmod(temp_file.name, 0o600)

            try:
                yield Path(temp_file.name)
            finally:
                try:
                    Path(temp_file.name).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")

    @retry_on_failure(
        max_retries=3,
        delay=0.5,
        backoff_factor=2.0,
        exceptions=(CookieDatabaseLockedError, CookieExtractionError),
    )
    def get_cookies_for_url(
        self,
        url: str,
        browser: str = "chrome",
        domain_only: bool = True,
        include_metadata: bool = False,
    ) -> dict[str, str] | dict[str, object]:
        """Extract cookies for a specific URL, iterating through preferred browsers."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Define preferred order
        preferred_browsers = [
            self._get_browser_type(browser),
            BrowserType.CHROME,
            BrowserType.FIREFOX,
        ]

        for b_type in preferred_browsers:
            if not b_type:
                continue

            result = self._extract_cookies_multisource(domain, b_type)
            if result.success:
                filtered = self._filter_valid_cookies(
                    result.cookies, domain, domain_only
                )
                return filtered

        return {}

    def _get_browser_type(self, browser: str) -> BrowserType | None:
        """Convert browser string to BrowserType enum."""
        browser_map = {
            "chrome": BrowserType.CHROME,
            "firefox": BrowserType.FIREFOX,
            "brave": BrowserType.BRAVE,
            "edge": BrowserType.EDGE,
            "opera": BrowserType.OPERA,
            "chrome_mobile": BrowserType.CHROME_MOBILE,
            "brave_mobile": BrowserType.BRAVE_MOBILE,
            "firefox_mobile": BrowserType.FIREFOX_MOBILE,
        }
        return browser_map.get(browser.lower())

    def _is_android(self) -> bool:
        """Check if running on Android/Termux."""
        return platform.system() == "Linux" and "termux" in os.environ.get("PREFIX", "")

    def _try_netscape_strategy(self, domain: str) -> ExtractionResult:
        """Try Netscape import strategy."""
        strategy = CookieExtractionFactory.get_strategy("netscape")
        return strategy.extract(domain)

    def _try_remaining_strategies(
        self, domain: str, browser_type: BrowserType
    ) -> ExtractionResult:
        """Try browser_cookie3, database, and cache."""
        if browser_cookie3 is not None:
            result = self._extract_with_browser_cookie3(domain, browser_type)
            if result.success:
                return result

        result = self._extract_from_database(domain, browser_type)
        if result.success:
            return result

        result = self._extract_from_cache()
        if result.success:
            return result

        return ExtractionResult(
            success=False, cookies={}, error="All extraction methods failed"
        )

    def _extract_cookies_multisource(
        self, domain: str, browser_type: BrowserType
    ) -> ExtractionResult:
        """Try multiple sources in order of preference, with Android fallback."""
        result = self._try_netscape_strategy(domain)
        if result.success:
            return result

        if self._is_android():
            logger.info(
                "Android environment detected. "
                "Bypassing browser-based cookie extraction."
            )
            return ExtractionResult(
                success=False,
                cookies={},
                error="Android detected, use OAuth2/cookies.txt",
            )

        return self._try_remaining_strategies(domain, browser_type)

    def load_cookies_from_file(self, cookie_file: Path) -> dict[str, str]:
        """Extract all cookies from a Netscape/Mozilla formatted cookies.txt file."""
        if not cookie_file.exists():
            return {}

        try:
            return self._parse_cookie_file(cookie_file)
        except Exception as e:
            logger.error(f"cookies.txt read failed: {e}")
            return {}

    def _parse_cookie_file(self, cookie_file: Path) -> dict[str, str]:
        cookies: dict[str, str] = {}
        with open(cookie_file, encoding="utf-8") as f:
            for line in f:
                parsed = self._parse_cookie_line(line.strip())
                if parsed:
                    cookies[parsed[0]] = parsed[1]
        return cookies

    def _parse_cookie_line(self, line: str) -> tuple[str, str] | None:
        if not line or line.startswith("#"):
            return None
        parts = line.split("\t")
        if len(parts) < 7:
            return None
        return (parts[5], parts[6])

    def _get_browser_cookie3_func(
        self, browser_type: BrowserType
    ) -> Callable[..., Any] | None:
        if browser_cookie3 is None:
            return None
        return {
            BrowserType.CHROME: browser_cookie3.chrome,
            BrowserType.FIREFOX: browser_cookie3.firefox,
            BrowserType.BRAVE: browser_cookie3.brave,
            BrowserType.EDGE: browser_cookie3.edge,
            BrowserType.OPERA: browser_cookie3.opera,
        }.get(browser_type)

    def _get_cj(self, cookie_func: Callable[..., Any], domain: str) -> Any:
        """Helper to get cookie jar."""
        if hasattr(cookie_func, "domain_name"):
            return cookie_func(domain_name=domain)
        return cookie_func()

    def _cj_to_cookies(self, cj: Any) -> dict[str, str]:
        """Helper to convert cookie jar to dict."""
        return {
            c.name: c.value for c in cj if hasattr(c, "name") and hasattr(c, "value")
        }

    def _extract_using_func(
        self, cookie_func: Callable[..., Any], domain: str
    ) -> ExtractionResult:
        """Helper to extract cookies using a provided browser_cookie3 function."""
        cj = self._get_cj(cookie_func, domain)
        if not cj:
            return ExtractionResult(success=False, cookies={}, error="No cookies")

        return ExtractionResult(
            success=True, cookies=self._cj_to_cookies(cj), source="browser_cookie3"
        )

    def _extract_with_browser_cookie3(
        self, domain: str, browser_type: BrowserType
    ) -> ExtractionResult:
        """Extract using browser_cookie3 with dynamic browser mapping."""
        if browser_cookie3 is None:
            return ExtractionResult(
                success=False, cookies={}, error="browser_cookie3 not available"
            )

        cookie_func = self._get_browser_cookie3_func(browser_type)
        if not cookie_func:
            return ExtractionResult(
                success=False, cookies={}, error=f"Unsupported: {browser_type}"
            )

        try:
            return self._extract_using_func(cookie_func, domain)
        except Exception as e:
            return ExtractionResult(
                success=False, cookies={}, error=f"browser_cookie3 failed: {e}"
            )

    def _get_system_key(self) -> str:
        """Determines the system key based on the current platform."""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        if system == "darwin":
            return "darwin"
        return "linux"

    def _run_extraction(
        self, cookie_path: Path, domain: str, browser_type: BrowserType
    ) -> ExtractionResult:
        """Runs the appropriate extraction based on browser type."""
        try:
            if browser_type == BrowserType.FIREFOX:
                return self._extract_firefox_cookies(cookie_path, domain)
            return self._extract_chrome_cookies(cookie_path, domain)
        except CookieDatabaseLockedError:
            raise
        except Exception as e:
            return ExtractionResult(
                success=False, cookies={}, error=f"Database extraction failed: {e}"
            )

    def _extract_from_database(
        self, domain: str, browser_type: BrowserType
    ) -> ExtractionResult:
        """Extract cookies directly from browser database."""
        system_key = self._get_system_key()

        browser_config = self.BROWSER_CONFIGS.get(browser_type)
        if not browser_config:
            return ExtractionResult(
                success=False, cookies={}, error=f"No configuration for {browser_type}"
            )

        cookie_path = browser_config.paths.get(system_key)
        if not cookie_path or not cookie_path.exists():
            return ExtractionResult(
                success=False,
                cookies={},
                error=f"Cookie database not found at {cookie_path}",
            )

        return self._run_extraction(cookie_path, domain, browser_type)

    def _process_chrome_row(
        self,
        row: sqlite3.Row,
        strategy: Any,
        cookies: dict[str, str],
        metadata: dict[str, CookieMetadata],
    ) -> None:
        """Process a single chrome cookie row."""
        name = row["name"]
        value = row["value"]
        if not value and row["encrypted_value"]:
            value = strategy.decrypt(row["encrypted_value"])
            if not value:
                return

        cookies[name] = value
        metadata[name] = CookieMetadata(
            expires=self._chrome_time_to_datetime(row["expires_utc"]),
            secure=bool(row["secure"]),
            domain=row["host_key"],
            path=row["path"] or "/",
            http_only=bool(row["httponly"]),
            same_site=row["samesite"],
        )

    def _extract_chrome_cookies(
        self, cookie_path: Path, domain: str
    ) -> ExtractionResult:
        """Extract cookies from Chrome-based browser using DecryptionStrategy."""
        from sota_dl.infrastructure.adapters.cookies import (
            DPAPIDecryptionStrategy,
            PassthroughDecryptionStrategy,
        )

        try:
            with (
                self._temp_file_copy(cookie_path) as temp_path,
                self._sqlite_connection(temp_path) as conn,
            ):
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, encrypted_value, value, host_key, "
                    "expires_utc, secure, httponly, path, samesite "
                    "FROM cookies WHERE host_key LIKE ?",
                    (f"%{domain}%",),
                )

                cookies: dict[str, str] = {}
                metadata: dict[str, CookieMetadata] = {}
                strategy = (
                    DPAPIDecryptionStrategy()
                    if platform.system() == "Windows"
                    else PassthroughDecryptionStrategy()
                )

                for row in cursor:
                    self._process_chrome_row(row, strategy, cookies, metadata)

                with self._metadata_lock:
                    self._cookie_metadata.update(metadata)

                return ExtractionResult(
                    success=True, cookies=cookies, metadata=metadata, source="chrome_db"
                )

        except Exception as e:
            return ExtractionResult(
                success=False, cookies={}, error=f"Chrome extraction failed: {e}"
            )

    def _decrypt_chrome_value(self, encrypted_value: bytes) -> str | None:
        """Decrypt Chrome's encrypted cookie values."""
        if not encrypted_value:
            return None

        try:
            system = platform.system()

            if system == "Windows":
                return self._decrypt_windows_dpapi(encrypted_value)
            elif system == "Darwin":
                return self._decrypt_macos_keychain(encrypted_value)
            else:
                return encrypted_value.decode("utf-8", errors="ignore")

        except Exception as e:
            logger.debug(f"Failed to decrypt Chrome value: {e}")
            return None

    def _decrypt_windows_dpapi(self, encrypted_value: bytes) -> str | None:
        """Decrypt using Windows DPAPI."""
        try:
            import win32crypt

            data = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[
                1
            ]
            return cast(bytes, data).decode("utf-8")
        except ImportError:
            logger.warning("win32crypt not available for DPAPI decryption")
            return None
        except Exception as e:
            logger.debug(f"DPAPI decryption failed: {e}")
            return None

    def _decrypt_macos_keychain(self, encrypted_value: bytes) -> str | None:
        """Decrypt using macOS Keychain."""
        logger.debug("macOS Keychain decryption not fully implemented")
        return None

    def _extract_firefox_cookies(
        self, profiles_path: Path, domain: str
    ) -> ExtractionResult:
        """Extract cookies from Firefox with proper profile detection."""
        try:
            profile_path = self._get_firefox_default_profile(profiles_path)
            if not profile_path:
                return ExtractionResult(
                    success=False, cookies={}, error="No Firefox profile found"
                )

            cookie_db = profile_path / "cookies.sqlite"
            if not cookie_db.exists():
                return ExtractionResult(
                    success=False,
                    cookies={},
                    error=f"Firefox cookie database not found: {cookie_db}",
                )

            return self._perform_firefox_extraction(cookie_db, domain)

        except CookieDatabaseLockedError:
            raise
        except Exception as e:
            return ExtractionResult(
                success=False, cookies={}, error=f"Firefox extraction failed: {e}"
            )

    def _perform_firefox_extraction(
        self, cookie_db: Path, domain: str
    ) -> ExtractionResult:
        with (
            self._temp_file_copy(cookie_db) as temp_path,
            self._sqlite_connection(temp_path) as conn,
        ):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    name, 
                    value, 
                    host, 
                    expiry, 
                    isSecure, 
                    isHttpOnly,
                    path,
                    sameSite
                FROM moz_cookies
                WHERE host LIKE ?
                """,
                (f"%{domain}%",),
            )

            cookies: dict[str, str] = {}
            metadata: dict[str, CookieMetadata] = {}

            for row in cursor:
                self._process_firefox_row(row, cookies, metadata)

            with self._metadata_lock:
                self._cookie_metadata.update(metadata)

            return ExtractionResult(
                success=True,
                cookies=cookies,
                metadata=metadata,
                source="firefox_db",
                extraction_time_ms=0.0,
            )

    def _process_firefox_row(
        self,
        row: sqlite3.Row,
        cookies: dict[str, str],
        metadata: dict[str, CookieMetadata],
    ) -> None:
        """Process a single row from Firefox cookies DB."""
        name = row["name"]
        cookies[name] = row["value"]

        expiry = row["expiry"]
        metadata[name] = CookieMetadata(
            expires=(
                datetime.fromtimestamp(expiry, tz=timezone.utc) if expiry else None
            ),
            secure=bool(row["isSecure"]),
            domain=row["host"],
            path=row["path"] or "/",
            http_only=bool(row["isHttpOnly"]),
            same_site=(str(row["sameSite"]) if row["sameSite"] else None),
        )

    def _get_firefox_default_profile(self, profiles_path: Path) -> Path | None:
        """Get the default Firefox profile using the new resolver."""

        # Using the new resolver to identify the root path if needed,
        # though firefox logic is specific to profile scanning.
        # This implementation simplifies the INI parsing.

        return self._parse_firefox_profiles_ini(profiles_path)

    def _get_default_profile_path(
        self, config: configparser.ConfigParser, profiles_path: Path
    ) -> Path | None:
        """Find the default profile path in config."""
        for section in config.sections():
            if config.getint(section, "Default", fallback=0) == 1:
                path = config.get(section, "Path")
                is_relative = config.getint(section, "IsRelative", fallback=1)
                profile_path = profiles_path / path if is_relative else Path(path)
                if profile_path.exists():
                    return profile_path
        return None

    def _parse_firefox_profiles_ini(self, profiles_path: Path) -> Path | None:
        """Helper to parse Firefox profiles.ini."""

        profiles_ini = profiles_path / "profiles.ini"

        if not profiles_ini.exists():
            profiles = list(profiles_path.glob("*.default*"))
            return profiles[0] if profiles else None

        config = configparser.ConfigParser()
        config.read(profiles_ini)

        return self._get_default_profile_path(config, profiles_path)

    def _extract_from_cache(self) -> ExtractionResult:
        """Extract cookies from encrypted cache file."""
        try:
            if not self.cookie_file.exists():
                return ExtractionResult(
                    success=False, cookies={}, error="No cached cookies available"
                )

            data = self._load_encrypted_cookies()
            if not data:
                return ExtractionResult(
                    success=False, cookies={}, error="Failed to extract from cache"
                )

            return self._process_cached_data(data)

        except Exception as e:
            logger.error(f"Cache extraction failed: {e}")
            return ExtractionResult(
                success=False, cookies={}, error="Failed to extract from cache"
            )

    def _process_cached_data(self, data: dict[str, Any]) -> ExtractionResult:
        cookies = data.get("cookies", {})
        metadata = data.get("metadata", {})

        self._check_cache_staleness(data.get("timestamp"))

        with self._metadata_lock:
            self._cookie_metadata.update(metadata)

        return ExtractionResult(
            success=True,
            cookies=cookies,
            metadata=metadata,
            source="encrypted_cache",
            extraction_time_ms=0.0,
        )

    def _check_cache_staleness(self, timestamp: str | None) -> None:
        if timestamp:
            cache_time = datetime.fromisoformat(timestamp)
            if datetime.now(timezone.utc) - cache_time > timedelta(hours=24):
                logger.warning("Using stale cached cookies (>24h old)")

    def _is_cookie_valid(
        self,
        name: str,
        value: str,
        domain: str,
        domain_only: bool,
        metadata: dict[str, CookieMetadata],
    ) -> bool:
        """Helper to validate a single cookie."""
        from sota_dl.infrastructure.adapters.cookies import CookieValidator

        cookie_meta = cast(CookieMetadata, metadata.get(name, {}))
        if self.validate_expiry or domain_only:
            return CookieValidator.is_valid(cookie_meta, domain if domain_only else "")
        return True

    def _filter_valid_cookies(
        self, cookies: dict[str, str], domain: str, domain_only: bool
    ) -> dict[str, str]:
        """Filter cookies by domain and expiry using CookieValidator."""
        filtered: dict[str, str] = {}

        with self._metadata_lock:
            metadata = self._cookie_metadata.copy()

        for name, value in cookies.items():
            if self._is_cookie_valid(name, value, domain, domain_only, metadata):
                filtered[name] = value

        return filtered

    def _chrome_time_to_datetime(self, chrome_time: int) -> datetime | None:
        """Convert Chrome/WebKit timestamp to UTC datetime."""
        if not chrome_time or chrome_time == 0:
            return None

        try:
            epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
            seconds = chrome_time / 1_000_000
            return epoch + timedelta(seconds=seconds)
        except (OverflowError, ValueError) as e:
            logger.warning(f"Invalid Chrome timestamp {chrome_time}: {e}")
            return None

    def _load_encrypted_cookies(self) -> dict[str, Any] | None:
        """Load and decrypt cookies from file."""
        with self._file_lock:
            try:
                return self._parse_and_validate_cookies()
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to load cookies: {e}")
                return None

    def _parse_and_validate_cookies(self) -> dict[str, Any] | None:
        if not self.cookie_file.exists():
            return None

        encrypted = self.cookie_file.read_bytes()
        if not encrypted:
            return None

        decrypted = self._decrypt_cookie_data(encrypted)
        data = json.loads(decrypted.decode("utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Invalid cookie data format")

        if "version" not in data:
            logger.warning("Loading legacy cookie format")

        return data

    def _decrypt_cookie_data(self, data: bytes) -> bytes:
        """Decrypts cookie data if encryption is enabled."""
        if not self.use_encryption:
            return data

        try:
            return self.fernet.decrypt(data)
        except InvalidToken as e:
            raise CookieSecurityError(
                "Failed to decrypt cookies - invalid token. "
                "Key may have changed or file is corrupted."
            ) from e
        except InvalidKey as e:
            raise CookieSecurityError("Failed to decrypt cookies - invalid key") from e

    def save_cookies_to_file(self, cookies: dict[str, str]) -> bool:
        """Save cookies to encrypted file with thread safety."""
        with self._file_lock:
            try:
                data = {
                    "cookies": cookies,
                    "metadata": dict(self._cookie_metadata),
                    "timestamp": (datetime.now(timezone.utc).isoformat()),
                    "version": "2.0",
                    "encryption_method": "fernet_v1",
                    "cookie_count": len(cookies),
                }

                json_data = json.dumps(data, indent=2).encode("utf-8")

                if self.use_encryption:
                    encrypted = self.fernet.encrypt(json_data)
                else:
                    encrypted = json_data

                temp_file = self.cookie_file.with_suffix(".tmp")
                temp_file.write_bytes(encrypted)
                temp_file.replace(self.cookie_file)

                logger.info(f"Saved {len(cookies)} cookies to {self.cookie_file}")
                return True

            except Exception as e:
                logger.error(f"Failed to save cookies: {e}")
                return False

    def clear_cookie_file(self) -> bool:
        """Securely delete the cookie file."""
        with self._file_lock:
            try:
                if self.cookie_file.exists():
                    file_size = self.cookie_file.stat().st_size
                    self.cookie_file.write_bytes(secrets.token_bytes(file_size))
                    self.cookie_file.unlink()

                    salt_file = self.cookie_file.parent / ".cookie_salt"
                    if salt_file.exists():
                        salt_file.unlink()

                    logger.info(f"Securely deleted cookie file: {self.cookie_file}")
                return True

            except Exception as e:
                logger.error(f"Failed to delete cookie file: {e}")
                return False

    def get_metrics(self) -> dict[str, object]:
        """Get adapter metrics for monitoring."""
        with self._metadata_lock:
            return {
                **self._metrics,
                "cached_cookie_count": len(self._cookie_metadata),
                "cookie_file_exists": self.cookie_file.exists(),
                "cookie_file_size": (
                    self.cookie_file.stat().st_size if self.cookie_file.exists() else 0
                ),
            }

    def __enter__(self) -> "BrowserCookieAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type:
            logger.error(f"Cookie adapter error: {exc_val}")


def get_cookies(
    url: str,
    browser: str = "chrome",
    use_encryption: bool = True,
    validate_expiry: bool = True,
) -> dict[str, str]:
    """Get cookies with default settings."""
    with BrowserCookieAdapter(
        use_encryption=use_encryption,
        validate_expiry=validate_expiry,
    ) as adapter:
        result = adapter.get_cookies_for_url(url, browser)
        return cast(dict[str, str], result)


def save_cookies(
    cookies: dict[str, str],
    cookie_file: Path | None = None,
    use_encryption: bool = True,
) -> bool:
    """Save cookies to file with default settings."""
    adapter = BrowserCookieAdapter(
        cookie_file=cookie_file,
        use_encryption=use_encryption,
    )
    return adapter.save_cookies_to_file(cookies)
