"""SOTA infrastructure exceptions – structured, loggable, and context‑rich."""

from __future__ import annotations

from typing import Any


class InfrastructureError(Exception):
    """
    Base exception for all infrastructure errors.

    Supports arbitrary keyword arguments that are stored as *details*
    and are shown in the string representation.  This makes the exception
    self‑documenting and easy to serialise for structured logging.

    Usage::

        raise InfrastructureError("Disk is full", path="/data", free_mb=42)
    """

    def __init__(self, message: str, **details: Any) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        base = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} [{details_str}]"
        return base

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r}, **{self.details!r})"

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary suitable for JSON logging."""
        return {
            "type": type(self).__name__,
            "message": self.message,
            "details": self.details,
        }


class DownloadError(InfrastructureError):
    """Raised when a download fails.

    Common details: *url*, *status_code*, *output_path*.
    """


class MergeError(InfrastructureError):
    """Raised when audio/video merging fails.

    Common details: *video_path*, *audio_path*, *output_path*, *ffmpeg_stderr*.
    """


class DRMError(InfrastructureError):
    """Raised for DRM decryption failures.

    Common details: *url*, *device_path*, *pssh*, *stderr*.
    """


class NetworkError(InfrastructureError):
    """Raised for network connectivity issues.

    Common details: *url*, *proxy*, *timeout*, *status_code*.
    """


class DiskSpaceError(InfrastructureError):
    """Raised when there is insufficient disk space.

    Common details: *path*, *required_bytes*, *free_bytes*.
    """


class ExtractionError(InfrastructureError):
    """Raised when metadata extraction fails.

    Common details: *url*, *reason*.
    """
