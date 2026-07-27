"""FFmpeg adapter exceptions."""


class FFmpegError(Exception):
    """Base exception for FFmpeg processing failures."""


class FFmpegNotFoundError(FFmpegError):
    """FFmpeg binary not found or not executable."""


class FFmpegProcessError(FFmpegError):
    """FFmpeg process returned a non‑zero exit code."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class FFmpegTimeoutError(FFmpegError):
    """Operation timed out."""
