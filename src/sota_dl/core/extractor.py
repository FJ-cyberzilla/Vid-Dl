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

from sota_dl.core.models.video_metadata import VideoMetadata
from sota_dl.core.protocols import MetadataCacheProtocol
from sota_dl.infrastructure.adapters.innertube import AndroidInnertubeAdapter
from sota_dl.core.event_bus import EventBus, ExtractorFallbackEvent
from sota_dl.utils.retry import RetryConfig, async_retry
from sota_dl.infrastructure.errors import ExtractionError

__all__ = ["MediaExtractor", "ExtractorConfig", "ExtractionError"]

logger = logging.getLogger("core.extractor")

# Keywords that indicate YouTube web bot blocks
BOT_BLOCK_KEYWORDS = [
    "sign in to confirm you're not a bot",
    "confirm you're not a robot",
    "http error 429",
    "http error 403",
    "too many requests",
    "bot check",
]


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
    Orchestrates metadata extraction with primary (yt-dlp) and fallback
    (Innertube) backends.
    """

    def __init__(
        self,
        cache: MetadataCacheProtocol,
        config: ExtractorConfig | None = None,
        retry_config: RetryConfig | None = None,
        innertube_adapter: AndroidInnertubeAdapter | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.cache = cache
        self.config = config or ExtractorConfig()
        self.retry_config = retry_config or RetryConfig(
            retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            retryable_exceptions=(ExtractionError, asyncio.TimeoutError),
        )
        self.innertube_adapter = innertube_adapter
        self.event_bus = event_bus

    async def extract_info(
        self, url: str, force_refresh: bool = False
    ) -> VideoMetadata:
        """Extracts video metadata with automatic fallback on bot blocks."""
        # 1. Primary Attempt: Standard yt-dlp extraction
        try:
            if not force_refresh:
                cached_data = await self.cache.get(url)
                if cached_data:
                    logger.info("Cache hit for metadata URL: %s", url)
                    return VideoMetadata(
                        title=cached_data.get("title", "Unknown"),
                        url=url,
                        video_id=cached_data.get("id"),
                        duration=cached_data.get("duration"),
                    )

            logger.info("Cache miss/refresh requested for URL: %s", url)
            data = await self._extract_with_retry(url)

            # Convert dict to VideoMetadata.
            metadata = VideoMetadata(
                title=data.get("title", "Unknown"),
                url=url,
                video_id=data.get("id"),
                duration=data.get("duration"),
            )

            # Store in cache as dict for compatibility with existing tests/storage
            await self.cache.set(url, data)
            return metadata

        except ExtractionError as exc:
            # 2. Check if the error was caused by bot detection / rate limiting
            if (
                self.innertube_adapter
                and self._is_bot_block_error(exc)
                and self._is_youtube_url(url)
            ):
                logger.warning(
                    f"Primary extractor blocked by YouTube bot protection for {url}. "
                    "Failing over to AndroidInnertubeAdapter..."
                )

                # Publish event so the UI can render an alert banner
                if self.event_bus:
                    await self.event_bus.publish(
                        ExtractorFallbackEvent(
                            url=url,
                            reason=str(exc),
                            fallback_target="Android Innertube API",
                        )
                    )

                return await self._extract_via_innertube(url)

            # Re-raise non-bot errors (e.g., 404 Video Deleted, Invalid URL)
            raise exc

    async def _extract_via_innertube(self, url: str) -> VideoMetadata:
        """Fallback execution path using raw Android API calls."""
        try:
            if not self.innertube_adapter:
                raise ExtractionError(
                    "Innertube adapter not configured", url=url, reason="No adapter"
                )

            metadata = await self.innertube_adapter.extract_metadata(url)
            logger.info(
                f"Successfully extracted metadata via Innertube for: {metadata.title}"
            )
            return metadata
        except Exception as exc:
            logger.error(f"Innertube fallback extraction failed: {exc}")
            raise ExtractionError(
                f"All extraction methods failed for {url}. "
                f"Primary blocked, Fallback error: {exc}",
                url=url,
                reason=str(exc),
            ) from exc

    def _is_bot_block_error(self, exc: Exception) -> bool:
        """Helper to check if an exception string contains bot block signatures."""
        err_msg = str(exc).lower()
        return any(keyword in err_msg for keyword in BOT_BLOCK_KEYWORDS)

    def _is_youtube_url(self, url: str) -> bool:
        """Helper to restrict Innertube fallback strictly to YouTube URLs."""
        return "youtube.com" in url or "youtu.be" in url

    # Keep original _extract_with_retry and _run_ytdlp_sync
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
                    raise ExtractionError(
                        f"yt-dlp returned empty info for URL: {url}",
                        url=url,
                        reason="Empty info",
                    )
                return cast(dict[str, Any], ydl.sanitize_info(info))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("yt-dlp execution error for %s: %s", url, exc)
            raise ExtractionError(
                f"Extraction failed: {exc}", url=url, reason=str(exc)
            ) from exc
