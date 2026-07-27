"""Psutil dependency helper."""

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    _PSUTIL_AVAILABLE = False
