"""Social media extractor – robust, async‑ready, with pluggable backends."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class ExtractionError(Exception):
    """Base exception for extraction failures."""


class UnsupportedPlatformError(ExtractionError):
    """The URL's platform is not supported by this extractor."""


class MissingDependencyError(ExtractionError):
    """Required backend library is not installed."""


class ExtractionTimeoutError(ExtractionError):
    """The extraction took too long."""


# ---------------------------------------------------------------------------
# Options container
# ---------------------------------------------------------------------------
@dataclass
class ExtractOptions:
    """Configuration for a media extraction operation.

    Attributes:
        output_format: Desired file extension / format (e.g., "mp4").
        progress_callback: Called periodically with a float percentage (0‑100).
        headers: Extra HTTP headers to pass to the backend.
        timeout: Maximum time (seconds) allowed for the entire extraction.
        retries: Number of retries on transient failures.
        quality: Preferred resolution, e.g., "720p", "best".
        extract_audio: If True, attempt to extract only the audio stream.
    """

    output_format: str = "mp4"
    progress_callback: Callable[[float], Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float | None = None
    retries: int = 3
    quality: str = "best"
    extract_audio: bool = False


# ---------------------------------------------------------------------------
# Abstract base – to be implemented by concrete backends (PyBalt, etc.)
# ---------------------------------------------------------------------------
class SocialMediaExtractor(ABC):
    """Abstract interface for social media extraction."""

    @abstractmethod
    def extract(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """Extract media from *url* and save to *output_path*."""

    @abstractmethod
    async def extract_async(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """Asynchronously extract media."""


# ---------------------------------------------------------------------------
# PyBalt engine – concrete implementation placeholder
# ---------------------------------------------------------------------------
class PyBaltEngine(SocialMediaExtractor):
    """
    Social media extractor powered by PyBalt (or any compatible backend).

    Currently raises :class:`MissingDependencyError` if PyBalt is not installed.
    Once the dependency is available, the stub logic in :meth:`_extract_impl`
    should be replaced with actual PyBalt calls.

    Usage (after implementation)::

        engine = PyBaltEngine()
        path = engine.extract(
            "https://twitter.com/user/status/123",
            Path("video.mp4"),
            options=ExtractOptions(progress_callback=lambda p: print(f"{p:.0f}%")),
        )
    """

    def __init__(self) -> None:
        """Check for PyBalt availability; defer error to extraction time."""
        self._pybalt_available = False
        with contextlib.suppress(ImportError):
            # Replace with real import when PyBalt is a real package
            # import pybalt
            # self._pybalt_available = True
            pass

    # ------------------------------------------------------------------
    # Core logic (placeholder)
    # ------------------------------------------------------------------
    def _extract_impl(
        self,
        _url: str,
        _output_path: Path,
        _options: ExtractOptions,
    ) -> Path:
        """
        Actual extraction logic. **Replace this with a real implementation.**
        """
        if not self._pybalt_available:
            raise MissingDependencyError(
                "PyBalt support requires additional dependencies.\n"
                "Install with: pip install pybalt  # (package name may differ)"
            )
        # Example pseudo‑call to a hypothetical PyBalt library
        # import pybalt
        # with pybalt.Client(...) as client:
        #     client.download(url, str(output_path), ...)
        raise NotImplementedError("Real PyBalt extraction logic not yet implemented.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def extract(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """
        Synchronously extract media from a social media URL.

        Args:
            url: The URL of the media post/page.
            output_path: Destination file path (parent directories are created).
            options: Extraction settings.

        Returns:
            The *output_path* where the media was saved.

        Raises:
            UnsupportedPlatformError: The URL is not recognised.
            MissingDependencyError: PyBalt (or chosen backend) is not installed.
            ExtractionTimeoutError: The operation timed out.
            ExtractionError: Other extraction failures.
        """
        if options is None:
            options = ExtractOptions()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Simple URL validation
        if not isinstance(url, str) or not url.strip():
            raise UnsupportedPlatformError("URL must be a non‑empty string.")

        # Retry loop – only retry transient ExtractionErrors
        for attempt in range(1, options.retries + 1):
            try:
                return self._extract_impl(url, output_path, options)
            except MissingDependencyError:
                raise  # not transient
            except ExtractionError as exc:
                if attempt == options.retries:
                    raise
                logger.warning(
                    "Extraction attempt %d failed: %s. Retrying...", attempt, exc
                )
                time.sleep(1.5 ** (attempt - 1))

        # Unreachable
        raise ExtractionError("Unexpected retry loop exit.")

    async def extract_async(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """
        Async wrapper around :meth:`extract`.

        Runs the blocking extraction in a thread pool so it doesn't block
        the event loop.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.extract,
            url,
            output_path,
            options,
        )
