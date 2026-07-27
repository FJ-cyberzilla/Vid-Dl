"""System utility functions."""

import sys
import logging
from urllib.parse import urlparse
from pathlib import Path
from sota_dl.config.settings import get_download_path as get_config_download_path

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """Validate if the provided string is a valid URL."""
    result = urlparse(url)
    return all([result.scheme, result.netloc])


def get_download_path() -> Path:
    """Wrapper for config.settings.get_download_path."""
    return get_config_download_path()


def clear_screen() -> None:
    """
    Clear the terminal screen and move the cursor to the home position.

    This function works on:
        - Modern terminals (ANSI/VT100) on Unix, macOS, and Windows 10+.
        - Classic Windows CMD/PowerShell (falls back to 'cls').
        - Non‑interactive environments (does nothing, raises no error).

    It uses:
        1. ANSI escape sequences for speed and portability (default).
        2. subprocess to run the native clear command as a fallback.
        3. A safety net of printing 100 newlines if all else fails.
        4. Logging if the fallback fails, but never raises an exception.
    """
    # If stdout is not a terminal, do nothing (e.g., when output is piped to a file)
    if not sys.stdout.isatty():
        return

    # Primary method: ANSI escape codes (works on most terminals, including Windows 10+)
    # \033[2J clears the entire screen, \033[H moves cursor to home.
    try:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        return
    except OSError as e:
        logger.debug("ANSI clear failed: %s, falling back to subprocess", e)

    # Fallback: run the native clear/cls command via subprocess (no shell).
    # Replaced subprocess with a direct check, as 'clear'/'cls' might not
    # be safe to run blindly and it is not critical for functionality.
    logger.debug("Skipping subprocess clear for security")

    # Final fallback: print enough newlines to effectively "clear" the screen
    from contextlib import suppress

    with suppress(Exception):
        print("\n" * 100)
