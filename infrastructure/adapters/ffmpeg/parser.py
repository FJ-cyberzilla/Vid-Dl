"""FFmpeg progress parsing utilities."""

import re

_FFMPEG_TIME_RE = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")


def parse_time(line: str) -> float | None:
    """Extract current processing time in seconds from an ffmpeg stderr line."""
    match = _FFMPEG_TIME_RE.search(line)
    if not match:
        return None
    h, m, s = match.group(1).split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)
