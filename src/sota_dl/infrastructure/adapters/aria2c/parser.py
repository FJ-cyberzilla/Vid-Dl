import re

_ARIA2_PROGRESS_RE = re.compile(r"\((\d+)%\)")  # e.g., "(25%)"


def _parse_progress(line: str) -> float | None:
    """Extract download percentage from an aria2c status line."""
    match = _ARIA2_PROGRESS_RE.search(line)
    if match:
        return float(match.group(1))
    return None
