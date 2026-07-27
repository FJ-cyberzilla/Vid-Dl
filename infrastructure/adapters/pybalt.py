"""Social media extractor – robust, async‑ready, with pluggable backends."""

from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from infrastructure.logger import setup_logger

logger = setup_logger("adapters.pybalt")

# Handle optional dependencies
try:
    from pybalt.core.exceptions import CobaltError
    from pybalt import StatusParent
except ImportError:
    # Define stubs if not available
    class CobaltError(Exception):
        """Stub for CobaltError."""

    class StatusParent:
        """Stub for StatusParent."""


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
    """Configuration for a media extraction operation."""

    output_format: str = "mp4"
    progress_callback: Callable[[float], Any] | None = None
    status_parent: Any | None = None  # Added for progress tracking
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float | None = None
    retries: int = 3
    quality: str = "best"
    extract_audio: bool = False
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Abstract base
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
# PyBalt engine – concrete implementation
# ---------------------------------------------------------------------------
class PyBaltEngine(SocialMediaExtractor):
    """Social media extractor powered by PyBalt."""

    def __init__(self, pybalt_client: Any = None) -> None:
        """Initialize with optional injected client."""
        self._client = pybalt_client
        if self._client is None:
            try:
                import pybalt

                self._client = pybalt
            except ImportError:
                self._client = None

    def _validate_input(self, url: str) -> None:
        """Validate input URL."""
        if not isinstance(url, str) or not url.strip():
            raise UnsupportedPlatformError("URL must be a non‑empty string.")

    async def _perform_extraction_async(
        self, url: str, output_path: Path, options: ExtractOptions
    ) -> Path:
        """Internal async logic for extraction."""
        if options.dry_run:
            logger.info("Dry run: Skipping extraction for %s", url)
            return output_path

        if self._client is None:
            raise MissingDependencyError("PyBalt library not found.")

        try:
            # Map options to pybalt
            kwargs = {
                "videoQuality": options.quality,
                "remux": True,
            }
            if options.extract_audio:
                kwargs["audioFormat"] = "mp3"

            # Pass progress tracker if provided
            if options.status_parent:
                kwargs["status_parent"] = options.status_parent

            # Perform download
            # pybalt.download returns the path of the downloaded file
            downloaded_path = await self._client.download(url, **kwargs)

            # Move to target output_path
            target_path = Path(downloaded_path)
            shutil.move(str(target_path), str(output_path))

            logger.info("Extracted %s to %s", url, output_path)
            return output_path

        except Exception as e:
            if isinstance(e, CobaltError):
                raise ExtractionError(f"PyBalt extraction failed: {e}") from e
            raise ExtractionError(f"Unexpected extraction error: {e}") from e

    def extract(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """Synchronously extract media."""
        return asyncio.run(self.extract_async(url, output_path, options))

    async def extract_async(
        self,
        url: str,
        output_path: Path,
        options: ExtractOptions | None = None,
    ) -> Path:
        """Asynchronously extract media with retries."""
        options = options or ExtractOptions()
        self._validate_input(url)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        retryer = retry(
            stop=stop_after_attempt(options.retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(ExtractionError),
            reraise=True,
        )

        return await retryer(self._perform_extraction_async)(url, output_path, options)
