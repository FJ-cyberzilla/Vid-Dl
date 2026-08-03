from .aria2c import Aria2cClient
from .ffmpeg import FFmpegProcessor
from .videodl import VideoDLFallback
from .yt_dlp import YtDlpAdapter

from typing import Any
import contextlib

PyBaltEngine: Any = None
with contextlib.suppress(ImportError):
    from ..extensions.pybalt import PyBaltEngine

WidevineDRM: Any = None
with contextlib.suppress(ImportError):
    from ..extensions.pywidevine import WidevineDRM

__all__ = [
    "Aria2cClient",
    "FFmpegProcessor",
    "PyBaltEngine",
    "WidevineDRM",
    "VideoDLFallback",
    "YtDlpAdapter",
]
