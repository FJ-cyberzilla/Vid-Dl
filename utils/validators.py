"""Input validation handlers."""

import re
import os


def is_valid_input(target: str) -> bool:
    """Validates standard HTTP/HTTPS URLs or local .txt files for batch processing."""
    if not target:
        return False

    target = target.strip()

    if os.path.isfile(target) and target.endswith(".txt"):
        return True

    regex = re.compile(
        r"^(?:http|ftp)s?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, target) is not None
