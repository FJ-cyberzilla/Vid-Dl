"""Environment and Application Configuration."""

import os
import shutil
from typing import NamedTuple


class AppConfig(NamedTuple):
    """Immutable application configuration."""
    gallery_dir: str = "/storage/emulated/0/DCIM/SOTADownloader"
    termux_fallback: str = os.path.expanduser("~/downloads/SOTADownloader")
    local_fallback: str = os.path.abspath("./downloads")


CONFIG = AppConfig()


def _resolve_path_option(path: str) -> bool:
    """Check if a directory is writeable without forcing creation."""
    if not os.path.exists(path):
        return False
    
    test_file = os.path.join(path, ".write_test")
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except (PermissionError, OSError):
        return False


def get_download_path() -> str:
    """Resolve the safest accessible storage path in Android without creating it."""
    # 1. Android Gallery
    if os.path.exists("/storage/emulated/0/DCIM"):
        if _resolve_path_option(CONFIG.gallery_dir):
            return CONFIG.gallery_dir

    # 2. Termux Fallback
    if _resolve_path_option(CONFIG.termux_fallback):
        return CONFIG.termux_fallback

    # 3. Local Workspace Fallback
    return CONFIG.local_fallback


def check_ffmpeg() -> bool:
    """Verify FFmpeg is installed and accessible in the system path."""
    return shutil.which("ffmpeg") is not None
