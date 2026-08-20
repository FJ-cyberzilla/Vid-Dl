"""Input validation handlers."""

import os
from pathlib import Path
from urllib.parse import urlparse

from sota_dl.config.settings import get_download_path as get_config_download_path
from sota_dl.core.models.download_options import DownloadOptions

# Supported URL schemes (extend as needed)
_SUPPORTED_SCHEMES = {"http", "https", "magnet", "file"}

# Case-insensitive batch file suffix
_BATCH_SUFFIX = ".txt"


def validate_url(url: str) -> bool:
    """Validate if the provided string is a valid URL."""
    result = urlparse(url)
    return all([result.scheme, result.netloc])


def get_download_path() -> Path:
    """Wrapper for config.settings.get_download_path."""
    return get_config_download_path()


...


def _is_valid_file_url(path: str) -> bool:
    """Validate a file:// URL path: must point to an existing .txt file."""
    path = _normalize_windows_path(path)
    return _is_batch_file(path)


def _normalize_windows_path(path: str) -> str:
    """Strips leading slash on Windows if present."""
    if os.name == "nt" and path.startswith("/"):
        return path[1:]
    return path


def _is_valid_url(target: str) -> bool:
    """Validate URL formats."""
    parsed = urlparse(target)
    if not _has_valid_scheme(parsed.scheme):
        return False

    if parsed.scheme == "file":
        return _is_valid_file_url(parsed.path)

    return bool(parsed.netloc)


def _has_valid_scheme(scheme: str) -> bool:
    """Checks if the URL scheme is supported."""
    return bool(scheme and scheme in _SUPPORTED_SCHEMES)


def is_valid_input(target: str) -> bool:
    """Validate user input for downloading or batch processing."""
    if not _is_non_empty_string(target):
        return False

    target = target.strip()
    if _is_batch_file(target):
        return True

    return _is_valid_url(target)


def _is_non_empty_string(target: str) -> bool:
    """Checks if target is a non-empty string."""
    return bool(target and target.strip())


def _is_batch_file(path: str) -> bool:
    """Checks if a path points to an existing batch file."""
    return path.lower().endswith(_BATCH_SUFFIX) and os.path.isfile(path)


def validate_options(options: DownloadOptions) -> bool:
    """Validate download options."""
    return hasattr(options, "output_dir")
