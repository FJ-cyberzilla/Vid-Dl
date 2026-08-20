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
from sota_dl.support.retry import RetryConfig, async_retry
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
        cached = await self._try_get_cached(url, force_refresh)
        if cached:
            return cached

        return await self._perform_extraction_flow(url)

    async def _try_get_cached(
        self, url: str, force_refresh: bool
    ) -> VideoMetadata | None:
        """Tries to get metadata from cache if not forcing refresh."""
        if force_refresh:
            return None
        return await self._get_cached_metadata(url)

    async def _perform_extraction_flow(self, url: str) -> VideoMetadata:
        """Executes the extraction, caching, and fallback flow."""
        try:
            logger.info("Cache miss/refresh requested for URL: %s", url)
            data = await self._extract_with_retry(url)
            metadata = self._create_metadata(url, data)
            await self.cache.set(url, data)
            return metadata
        except ExtractionError as exc:
            return await self._handle_fallback(url, exc)

    async def _get_cached_metadata(self, url: str) -> VideoMetadata | None:
        """Retrieves and converts cached metadata if available."""
        cached_data = await self.cache.get(url)
        if not cached_data:
            return None
        logger.info("Cache hit for metadata URL: %s", url)
        return self._create_metadata(url, cached_data)

    def _create_metadata(self, url: str, data: dict[str, Any]) -> VideoMetadata:
        """Converts raw extractor data into VideoMetadata object."""
        return VideoMetadata(
            title=cast(str, data.get("title", "Unknown")),
            url=url,
            video_id=cast(str | None, data.get("id")),
            duration=cast(int | None, data.get("duration")),
        )

    async def _handle_fallback(self, url: str, exc: ExtractionError) -> VideoMetadata:
        """Handles failover to secondary extraction methods on bot blocks."""
        if not self._should_fallback(url, exc):
            raise exc

        logger.warning(
            f"Primary extractor blocked for {url}. "
            "Failing over to AndroidInnertubeAdapter..."
        )

        await self._notify_fallback(url, exc)
        return await self._extract_via_innertube(url)

    def _should_fallback(self, url: str, exc: ExtractionError) -> bool:
        """Determines if fallback should be attempted."""
        return bool(
            self.innertube_adapter
            and self._is_bot_block_error(exc)
            and self._is_youtube_url(url)
        )

    async def _notify_fallback(self, url: str, exc: ExtractionError) -> None:
        """Publishes fallback event if event bus is available."""
        if not self.event_bus:
            return

        await self.event_bus.publish(
            ExtractorFallbackEvent(
                url=url,
                reason=str(exc),
                fallback_target="Android Innertube API",
            )
        )

    async def _extract_via_innertube(self, url: str) -> VideoMetadata:
        """Fallback execution path using raw Android API calls."""
        try:
            return await self._execute_innertube_extraction(url)
        except Exception as exc:
            logger.error(f"Innertube fallback extraction failed: {exc}")
            raise ExtractionError(
                f"All extraction methods failed for {url}. "
                f"Fallback error: {exc}",
                url=url,
                reason=str(exc),
            ) from exc

    async def _execute_innertube_extraction(self, url: str) -> VideoMetadata:
        """Internal helper to execute innertube extraction."""
        if not self.innertube_adapter:
            raise ExtractionError(
                "Innertube adapter not configured", url=url, reason="No adapter"
            )
        return await self.innertube_adapter.extract_metadata(url)

    def _is_bot_block_error(self, exc: Exception) -> bool:
        """Helper to check if an exception string contains bot block signatures."""
        err_msg = str(exc).lower()
        return any(keyword in err_msg for keyword in BOT_BLOCK_KEYWORDS)

    def _is_youtube_url(self, url: str) -> bool:
        """Helper to restrict Innertube fallback strictly to YouTube URLs."""
        return "youtube.com" in url or "youtu.be" in url

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
        opts = self._build_ydl_opts()
        try:
            return self._execute_ytdlp_extraction(url, opts)
        except Exception as exc:
            logger.error("yt-dlp execution error for %s: %s", url, exc)
            raise ExtractionError(
                f"Extraction failed: {exc}", url=url, reason=str(exc)
            ) from exc

    def _build_ydl_opts(self) -> dict[str, Any]:
        """Builds yt-dlp options dictionary."""
        opts: dict[str, Any] = {
            "extract_flat": "in_playlist" if self.config.download_flat else False,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
        }
        if self.config.extra_options:
            opts.update(self.config.extra_options)
        return opts

    def _execute_ytdlp_extraction(
        self, url: str, opts: dict[str, Any]
    ) -> dict[str, Any]:
        """Executes the raw yt-dlp extraction."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ExtractionError(
                    f"yt-dlp returned empty info for URL: {url}",
                    url=url,
                    reason="Empty info",
                )
            return cast(dict[str, Any], ydl.sanitize_info(info))
