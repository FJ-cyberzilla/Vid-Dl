"""FFmpeg adapter package."""

from .exceptions import (
    FFmpegError,
    FFmpegNotFoundError,
    FFmpegProcessError,
    FFmpegTimeoutError,
)
from .parser import parse_time
from .processor import FFmpegProcessor

__all__ = [
    "FFmpegError",
    "FFmpegNotFoundError",
    "FFmpegProcessError",
    "FFmpegTimeoutError",
    "FFmpegProcessor",
    "parse_time",
]
