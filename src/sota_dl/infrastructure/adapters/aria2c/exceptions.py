class Aria2cError(Exception):
    """Base exception for aria2c failures."""


class Aria2cNotFoundError(Aria2cError):
    """The aria2c binary is not installed or not found."""


class Aria2cProcessError(Aria2cError):
    """aria2c returned a non‑zero exit code."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class Aria2cTimeoutError(Aria2cError):
    """The download timed out."""
