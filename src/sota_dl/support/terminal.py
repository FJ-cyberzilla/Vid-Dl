"""System utility functions."""

import sys
import logging

logger = logging.getLogger(__name__)


def clear_screen() -> None:
    """
        Clear the terminal screen and move the cursor to the home position.
    ...
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
