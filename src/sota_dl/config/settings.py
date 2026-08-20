"""Environment and Application Configuration."""

import os
import shutil
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# ---- Android defaults (keep as original) ----
ANDROID_GALLERY_DIR = Path("/storage/emulated/0/DCIM/SOTADownloader")
TERMUX_FALLBACK = Path("~").expanduser() / "downloads" / "SOTADownloader"
LOCAL_FALLBACK = Path("./downloads").absolute()

# ---- Environment override ----
_ENV_OVERRIDE = os.getenv("SOTA_DOWNLOAD_DIR")
if _ENV_OVERRIDE:
    ENV_OVERRIDE_PATH: Path | None = Path(_ENV_OVERRIDE).expanduser().absolute()
else:
    ENV_OVERRIDE_PATH = None

# ---- Cache for writability checks ----

_WRITABLE_CACHE: dict[Path, bool] = {}

# ---- OAuth Credentials ----
OAUTH_CLIENT_ID = os.getenv("SOTA_OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.getenv("SOTA_OAUTH_CLIENT_SECRET", "")
ACCESS_TOKEN: str | None = None
REFRESH_TOKEN: str | None = None
COOKIES_PATH = Path("cookies.txt")
TIMEOUT = 30
DEBUG = False


def _is_writable(path: Path) -> bool:
    """
    Check if a directory is writable, with caching.
    Also creates the directory if it doesn't exist.
    """
    if path in _WRITABLE_CACHE:
        return _WRITABLE_CACHE[path]

    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        _WRITABLE_CACHE[path] = True
        return True
    except (PermissionError, OSError):
        _WRITABLE_CACHE[path] = False
        return False


class Settings:
    """Wrapper for global application configuration."""

    @property
    def COOKIES_PATH(self) -> Path:
        return COOKIES_PATH

    @COOKIES_PATH.setter
    def COOKIES_PATH(self, value: Path) -> None:
        global COOKIES_PATH
        COOKIES_PATH = value

    @property
    def ENV_OVERRIDE(self) -> Path | None:
        return ENV_OVERRIDE_PATH

    @ENV_OVERRIDE.setter
    def ENV_OVERRIDE(self, value: Path | None) -> None:
        global ENV_OVERRIDE_PATH
        ENV_OVERRIDE_PATH = value

    @property
    def OAUTH_CLIENT_ID(self) -> str:
        return OAUTH_CLIENT_ID

    @property
    def OAUTH_CLIENT_SECRET(self) -> str:
        return OAUTH_CLIENT_SECRET

    @property
    def ACCESS_TOKEN(self) -> str | None:
        return ACCESS_TOKEN

    @ACCESS_TOKEN.setter
    def ACCESS_TOKEN(self, value: str | None) -> None:
        global ACCESS_TOKEN
        ACCESS_TOKEN = value

    @property
    def REFRESH_TOKEN(self) -> str | None:
        return REFRESH_TOKEN

    @REFRESH_TOKEN.setter
    def REFRESH_TOKEN(self, value: str | None) -> None:
        global REFRESH_TOKEN
        REFRESH_TOKEN = value

    @property
    def TIMEOUT(self) -> int:
        return TIMEOUT

    @TIMEOUT.setter
    def TIMEOUT(self, value: int) -> None:
        global TIMEOUT
        TIMEOUT = value

    @property
    def DEBUG(self) -> bool:
        return DEBUG

    @DEBUG.setter
    def DEBUG(self, value: bool) -> None:
        global DEBUG
        DEBUG = value

    def _is_writable(self, path: Path) -> bool:
        return _is_writable(path)

    def get_download_path(self) -> Path:
        return get_download_path()


settings = Settings()


def _find_writable_path(candidates: list[tuple[Path, str]]) -> Path | None:
    """Find the first writable path from a list of candidates."""
    for path, label in candidates:
        if label == "Android Gallery" and not ANDROID_GALLERY_DIR.parent.exists():
            continue
        if _is_writable(path):
            logger.info("Using %s download path: %s", label, path)
            return path
    return None


def get_download_path() -> Path:
    """
    Resolve the safest accessible download path, with priority:
        1. Environment variable SOTA_DOWNLOAD_DIR (if set)
        2. Android Gallery (if exists and writable)
        3. Termux fallback (if writable)
        4. Local fallback (./downloads) – always falls back
    Returns an absolute Path; ensures the directory exists.
    """
    candidates = []
    if ENV_OVERRIDE_PATH:
        candidates.append((ENV_OVERRIDE_PATH, "env override"))
    candidates.append((ANDROID_GALLERY_DIR, "Android Gallery"))
    candidates.append((TERMUX_FALLBACK, "Termux fallback"))

    path = _find_writable_path(candidates)
    if path:
        return path

    # Priority 3: Local fallback (always works, we create it)
    if not LOCAL_FALLBACK.exists():
        LOCAL_FALLBACK.mkdir(parents=True, exist_ok=True)
    logger.info("Using local fallback path: %s", LOCAL_FALLBACK)
    return LOCAL_FALLBACK


def _parse_ffmpeg_version(first_line: str) -> bool:
    """Parse FFmpeg version string and return True if >= 4.0."""
    try:
        parts = first_line.split()
        for part in parts:
            if part[0].isdigit():
                version_str = part.split("-")[0]  # e.g., "4.4.2"
                major = int(version_str.split(".")[0])
                return major >= 4
    except (ValueError, IndexError):
        pass
    return True  # if we can't parse, assume OK


def check_ffmpeg(version_check: bool = True) -> bool:
    """
    Verify FFmpeg is installed and (optionally) that it meets a minimum version.
    Returns True if found and, if version_check is True, version ≥ 4.0.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        return False

    if not version_check:
        return True

    # Optional: verify version ≥ 4.0 (which supports most features)
    try:
        result = subprocess.run(  # nosec B603
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return True  # command failed, but ffmpeg exists – assume OK
        return _parse_ffmpeg_version(result.stdout.splitlines()[0])
    except (OSError, AttributeError):
        return True
