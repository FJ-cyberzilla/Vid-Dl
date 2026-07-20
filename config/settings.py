"""Environment and Application Configuration."""

import os
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# ---- Android defaults (keep as original) ----
ANDROID_GALLERY_DIR = Path("/storage/emulated/0/DCIM/SOTADownloader")
TERMUX_FALLBACK = Path(os.path.expanduser("~/downloads/SOTADownloader"))
LOCAL_FALLBACK = Path("./downloads").absolute()

# ---- Environment override ----
_ENV_OVERRIDE = os.getenv("SOTA_DOWNLOAD_DIR")
if _ENV_OVERRIDE:
    ENV_OVERRIDE = Path(_ENV_OVERRIDE).expanduser().absolute()
else:
    ENV_OVERRIDE = None

# ---- Cache for writability checks ----
_WRITABLE_CACHE: Dict[Path, bool] = {}

# ---- Cookies ----
# Default to 'cookies.txt' in the project root (relative to this file's parent's parent)
DEFAULT_COOKIES = Path(__file__).parent.parent / "cookies.txt"
COOKIES_ENV_OVERRIDE = os.getenv("SOTA_COOKIES")

if COOKIES_ENV_OVERRIDE:
    COOKIES_PATH = Path(COOKIES_ENV_OVERRIDE).expanduser().absolute()
else:
    COOKIES_PATH = DEFAULT_COOKIES.absolute()


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


def get_download_path() -> Path:
    """
    Resolve the safest accessible download path, with priority:
        1. Environment variable SOTA_DOWNLOAD_DIR (if set)
        2. Android Gallery (if exists and writable)
        3. Termux fallback (if writable)
        4. Local fallback (./downloads) – always falls back
    Returns an absolute Path; ensures the directory exists.
    """
    # Priority 0: environment override
    if ENV_OVERRIDE is not None:
        if _is_writable(ENV_OVERRIDE):
            logger.info("Using env override download path: %s", ENV_OVERRIDE)
            return ENV_OVERRIDE
        logger.warning(
            "Env override path %s is not writable; falling back.", ENV_OVERRIDE
        )

    # Priority 1: Android Gallery
    if ANDROID_GALLERY_DIR.parent.exists():  # check /storage/emulated/0/DCIM exists
        if _is_writable(ANDROID_GALLERY_DIR):
            logger.info("Using Android Gallery path: %s", ANDROID_GALLERY_DIR)
            return ANDROID_GALLERY_DIR

    # Priority 2: Termux fallback
    if _is_writable(TERMUX_FALLBACK):
        logger.info("Using Termux fallback path: %s", TERMUX_FALLBACK)
        return TERMUX_FALLBACK

    # Priority 3: Local fallback (always works, we create it)
    if not LOCAL_FALLBACK.exists():
        LOCAL_FALLBACK.mkdir(parents=True, exist_ok=True)
    logger.info("Using local fallback path: %s", LOCAL_FALLBACK)
    return LOCAL_FALLBACK


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
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,  # explicit to avoid W1510
        )
        if result.returncode != 0:
            return True  # command failed, but ffmpeg exists – assume OK
        first_line = result.stdout.splitlines()[0]
        # e.g., "ffmpeg version 4.4.2 ..." -> extract version
        parts = first_line.split()
        for part in parts:
            if part[0].isdigit():
                version_str = part.split("-")[0]  # e.g., "4.4.2"
                major = int(version_str.split(".")[0])
                return major >= 4
        return True  # if we can't parse, assume OK
    except Exception:
        # If version check fails, still assume it's available
        return True
