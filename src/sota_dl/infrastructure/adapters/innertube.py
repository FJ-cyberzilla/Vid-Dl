# src/sota_dl/infrastructure/adapters/innertube.py

import structlog
import urllib.parse
from typing import Any

from sota_dl.core.models.video_metadata import VideoMetadata
from sota_dl.infrastructure.errors import ExtractionError
from sota_dl.infrastructure.network import NetworkManager

logger = structlog.get_logger(__name__)


class AndroidInnertubeAdapter:
    """
    Direct REST client for YouTube's internal Innertube API.
    Emulates the official Android YouTube app to bypass web-based bot checks.
    """

    API_URL = "https://youtubei.googleapis.com/youtubei/v1/player"

    # Official Android App identifiers
    CLIENT_NAME = "ANDROID"
    CLIENT_VERSION = "19.29.37"
    OS_VERSION = "13"

    def __init__(self, network_manager: NetworkManager):
        self.network_manager = network_manager
        # The exact headers the Android app sends
        user_agent = (
            f"com.google.android.youtube/{self.CLIENT_VERSION} "
            f"(Linux; U; Android {self.OS_VERSION}; gzip)"
        )
        self.headers = {
            "User-Agent": user_agent,
            "X-YouTube-Client-Name": "3",  # 3 = Android
            "X-YouTube-Client-Version": self.CLIENT_VERSION,
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
        }
        logger.debug("AndroidInnertubeAdapter initialized")

    def _build_android_context(self) -> dict[str, Any]:
        """Constructs the Innertube context payload."""
        return {
            "client": {
                "clientName": self.CLIENT_NAME,
                "clientVersion": self.CLIENT_VERSION,
                "androidSdkVersion": 33,
                "osName": "Android",
                "osVersion": self.OS_VERSION,
                "hl": "en",
                "gl": "US",
            }
        }

    async def extract_metadata(self, video_url: str) -> VideoMetadata:
        """Extracts video metadata and stream formats directly from Innertube."""
        video_id = self._extract_video_id(video_url)
        if not video_id:
            logger.error("Failed to parse video ID", url=video_url)
            raise ExtractionError(
                f"Could not parse video ID from: {video_url}",
                url=video_url,
                reason="Invalid URL",
            )

        payload = {
            "context": self._build_android_context(),
            "videoId": video_id,
            "playbackContext": {
                "contentPlaybackContext": {"html5Preference": "HTML5_PREF_WANTS"}
            },
        }

        # Use network_manager.throttled_request to perform sync post request
        try:
            response = await self.network_manager.throttled_request(
                self.network_manager.session.post,
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(
                "Innertube API request failed",
                video_id=video_id,
                error=str(e),
            )
            raise ExtractionError(
                f"Innertube API request error: {e}", url=video_url, reason=str(e)
            ) from e

        return self._parse_player_response(data, video_url)

    def _extract_video_id(self, url: str) -> str | None:
        """Extracts the 11-character video ID from a YouTube URL."""
        parsed = urllib.parse.urlparse(url)
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/")
        if "youtube.com" in parsed.netloc:
            qs = urllib.parse.parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        return None

    def _parse_player_response(
        self, data: dict[str, Any], original_url: str
    ) -> VideoMetadata:
        """Maps the raw Innertube JSON to sota_dl's VideoMetadata model."""

        playability = data.get("playabilityStatus", {})
        if playability.get("status") != "OK":
            reason = playability.get("reason", "Unknown block")
            logger.warning(
                "Video unplayable via Android client",
                url=original_url,
                reason=reason,
            )
            raise ExtractionError(
                f"Video unplayable via Android client: {reason}",
                url=original_url,
                reason=reason,
            )

        details = data.get("videoDetails", {})
        streaming_data = data.get("streamingData", {})

        # Extract direct stream URLs
        formats = streaming_data.get("formats", [])
        adaptive_formats = streaming_data.get("adaptiveFormats", [])

        # Merge all formats for the fallback downloader to pick from
        all_streams = []
        for fmt in formats + adaptive_formats:
            # Note: Some streams use 'signatureCipher' instead of 'url'.
            # We skip ciphered streams here unless you build a decryptor.
            if "url" in fmt:
                all_streams.append(
                    {
                        "url": fmt["url"],
                        "quality": fmt.get("qualityLabel") or fmt.get("audioQuality"),
                        "mimeType": fmt.get("mimeType"),
                        "bitrate": fmt.get("bitrate"),
                        "contentLength": fmt.get("contentLength"),
                    }
                )

        if not all_streams:
            logger.warning("No direct URLs found", url=original_url)
            raise ExtractionError(
                "No direct URLs found. Stream might be DRM/Cipher protected.",
                url=original_url,
                reason="No direct URLs",
            )

        # Map to sota_dl protocol
        return VideoMetadata(
            title=details.get("title", "Unknown Title"),
            url=original_url,  # Compatible with original model
            webpage_url=original_url,
            duration=int(details.get("lengthSeconds", 0)),
            uploader=details.get("author", "Unknown"),
            view_count=int(details.get("viewCount", 0)),
            formats=all_streams,
        )
