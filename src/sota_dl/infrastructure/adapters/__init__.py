from .aria2c import Aria2cClient
from .ffmpeg import FFmpegProcessor
from .videodl import VideoDLFallback
from .yt_dlp import YtDlpAdapter

try:
    from ..extensions.pybalt import PyBaltEngine
except ImportError:
    PyBaltEngine = None

try:
    from ..extensions.pywidevine import WidevineDRM
except ImportError:
    WidevineDRM = None

__all__ = [
    "Aria2cClient",
    "FFmpegProcessor",
    "PyBaltEngine",
    "WidevineDRM",
    "VideoDLFallback",
    "YtDlpAdapter",
]
