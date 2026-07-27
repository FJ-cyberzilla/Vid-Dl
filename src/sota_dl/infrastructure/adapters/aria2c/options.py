from dataclasses import dataclass
from typing import Any
from collections.abc import Callable


@dataclass
class Aria2cOptions:
    """Configuration for a single download.

    Attributes:
        max_connections: Number of parallel connections (default 16).
        chunk_size: Chunk size passed to aria2c, e.g., ``"1M"``.
        timeout: Maximum time in seconds to wait for the download.
        retries: Number of retries on transient failures.
        progress_callback: Called with a percentage (0‑100) as download advances.
        headers: Extra HTTP headers as a dict.
    """

    max_connections: int = 16
    chunk_size: str = "1M"
    timeout: float | None = None
    retries: int = 3
    progress_callback: Callable[[float], Any] | None = None
    headers: dict[str, str] | None = None
