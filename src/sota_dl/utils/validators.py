"""Input validation handlers."""

import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

# Supported URL schemes (extend as needed)
_SUPPORTED_SCHEMES = {"http", "https", "magnet", "file"}

# Case-insensitive batch file suffix
_BATCH_SUFFIX = ".txt"


def _is_valid_file_url(path: str) -> bool:
    """
    Validate a file:// URL path: must point to an existing .txt file.
    Handles both Windows and POSIX paths.
    """
    if os.name == "nt" and path.startswith("/"):
        path = path[1:]  # strip leading slash on Windows
    return path.lower().endswith(_BATCH_SUFFIX) and Path(path).is_file()


def _is_valid_url(target: str) -> bool:
    """Validate URL formats."""
    parsed = urlparse(target)
    if not parsed.scheme or parsed.scheme not in _SUPPORTED_SCHEMES:
        return False
    if parsed.scheme == "file":
        return _is_valid_file_url(parsed.path)
    return bool(parsed.netloc)


def is_valid_input(target: str) -> bool:
    """
    Validate user input for downloading or batch processing.
    """
    if not target or not target.strip():
        return False

    target = target.strip()

    if target.lower().endswith(_BATCH_SUFFIX) and os.path.isfile(target):
        return True

    return _is_valid_url(target)


def validate_options(options: Any) -> bool:
    """Validate download options."""
    return hasattr(options, "output_dir")
