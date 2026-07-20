"""Input validation handlers."""

import os
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
    return path.lower().endswith(_BATCH_SUFFIX) and os.path.isfile(path)


def is_valid_input(target: str) -> bool:
    """
    Validate user input for downloading or batch processing.

    Accepts:
        - HTTP/HTTPS/FTP URLs (with scheme and netloc).
        - Magnet links (magnet:?xt=...).
        - Local batch files (.txt, case-insensitive) that exist on disk.
        - file:// URLs pointing to existing .txt files.

    Returns:
        True if the input is considered valid, False otherwise.
    """
    # Reject empty or whitespace-only input early
    if not target or not target.strip():
        return False

    target = target.strip()

    # Batch file: local .txt file
    if target.lower().endswith(_BATCH_SUFFIX) and os.path.isfile(target):
        return True

    # URL validation
    try:
        parsed = urlparse(target)
    except Exception:
        return False

    # Must have a scheme and it must be supported
    if not parsed.scheme or parsed.scheme not in _SUPPORTED_SCHEMES:
        return False

    # Special case: file:// – must point to a valid .txt file
    if parsed.scheme == "file":
        return _is_valid_file_url(parsed.path)

    # For other schemes (http, https, ftp, magnet), require a non-empty netloc
    return bool(parsed.netloc)

def validate_options(options: Any) -> bool:
    """Validate download options."""
    # Placeholder for actual validation logic if needed in the future
    return hasattr(options, "output_dir")
