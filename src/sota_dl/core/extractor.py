"""
Core - Media Metadata Extractor
Integrates yt-dlp metadata extraction with persistent caching, async retries,
and file logging.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, cast

import yt_dlp

from sota_dl.core.protocols import MetadataCacheProtocol
from sota_dl.utils.retry import RetryConfig, async_retry

logger = logging.getLogger("core.extractor")


class ExtractionError(Exception):
    """Raised when media metadata extraction fails after retries."""


@dataclass(slots=True, frozen=True)
class ExtractorConfig:
    """Configuration options for the media metadata extractor."""

    download_flat: bool = True
    process_playlist: bool = False
    extra_options: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representation of the extractor configuration."""
        return {
            "download_flat": self.download_flat,
            "process_playlist": self.process_playlist,
            "extra_options": self.extra_options or {},
        }


class MediaExtractor:
    """
    Extracts video and audio metadata using yt-dlp with caching, retries,
    and logging.
    """

    def __init__(
        self,
        cache: MetadataCacheProtocol,
        config: ExtractorConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self.cache = cache
        self.config = config or ExtractorConfig()
        self.retry_config = retry_config or RetryConfig(
            retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            retryable_exceptions=(ExtractionError, asyncio.TimeoutError),
        )

    async def extract_info(
        self, url: str, force_refresh: bool = False
    ) -> dict[str, Any]:
        """
        Extracts metadata for a given URL, utilizing cache unless
        force_refresh is True.
        """
        if not force_refresh:
            cached_data = await self.cache.get(url)
            if cached_data:
                logger.info("Cache hit for metadata URL: %s", url)
                return cached_data

        logger.info("Cache miss/refresh requested for URL: %s", url)
        data = await self._extract_with_retry(url)

        await self.cache.set(url, data)
        return data

    async def clear_cache(self) -> None:
        """Clears all cached metadata from the underlying metadata storage."""
        logger.info("Clearing metadata extraction cache.")
        await self.cache.clear()

    async def _extract_with_retry(self, url: str) -> dict[str, Any]:
        """Wraps raw extraction with the async retry decorator."""

        @async_retry(
            config=self.retry_config,
            on_retry=lambda exc, attempt, delay: logger.warning(
                "Metadata extraction attempt %d failed for %s. "
                "Retrying in %.2fs. Error: %s",
                attempt,
                url,
                delay,
                exc,
            ),
        )
        async def _do_extract() -> dict[str, Any]:
            return await asyncio.to_thread(self._run_ytdlp_sync, url)

        return await _do_extract()

    def _run_ytdlp_sync(self, url: str) -> dict[str, Any]:
        """Executes yt-dlp extraction synchronously in a separate thread."""
        ydl_opts: dict[str, Any] = {
            "extract_flat": "in_playlist" if self.config.download_flat else False,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
        }

        if self.config.extra_options:
            ydl_opts.update(self.config.extra_options)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    raise ExtractionError(f"yt-dlp returned empty info for URL: {url}")
                return cast(dict[str, Any], ydl.sanitize_info(info))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("yt-dlp execution error for %s: %s", url, exc)
            raise ExtractionError(f"Extraction failed: {exc}") from exc
