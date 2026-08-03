"""Tests for MediaExtractor."""

from unittest.mock import patch
from pathlib import Path
from typing import Any
import pytest
from sota_dl.core.extractor import MediaExtractor, ExtractorConfig, ExtractionError
from sota_dl.infrastructure.cache.cache_manager import CacheManager
from sota_dl.infrastructure.cache.async_adapter import AsyncCacheAdapter


@pytest.mark.asyncio
async def test_extractor_cache_hit(tmp_path: Path) -> None:
    cache_manager = CacheManager(cache_dir=tmp_path / "cache")
    cache = AsyncCacheAdapter(cache_manager)
    await cache.set("https://example.com/test", {"id": "123", "title": "Test Title"})

    extractor = MediaExtractor(cache=cache)
    info = await extractor.extract_info("https://example.com/test")

    assert info.video_id == "123"
    assert info.title == "Test Title"


@pytest.mark.asyncio
async def test_extractor_ytdlp_success(tmp_path: Path) -> None:
    cache_manager = CacheManager(cache_dir=tmp_path / "cache")
    cache = AsyncCacheAdapter(cache_manager)
    extractor = MediaExtractor(cache=cache)

    mock_info = {"id": "v999", "title": "Extracted Title"}

    with patch.object(
        extractor, "_run_ytdlp_sync", return_value=mock_info
    ) as mock_sync:
        info = await extractor.extract_info("https://example.com/new_video")

        assert info.video_id == "v999"
        mock_sync.assert_called_once_with("https://example.com/new_video")

        # Verify it was written to cache
        cached = await cache.get("https://example.com/new_video")
        assert cached == mock_info


def test_extractor_config_to_dict() -> None:
    config = ExtractorConfig(download_flat=False, extra_options={"test": 1})
    d = config.to_dict()
    assert d["download_flat"] is False
    assert d["extra_options"] == {"test": 1}


@patch("yt_dlp.YoutubeDL")
def test_run_ytdlp_sync_failure(mock_ytdl: Any, tmp_path: Path) -> None:
    cache_manager = CacheManager(cache_dir=tmp_path / "cache")
    cache = AsyncCacheAdapter(cache_manager)
    extractor = MediaExtractor(cache=cache)

    mock_instance = mock_ytdl.return_value.__enter__.return_value
    mock_instance.extract_info.side_effect = Exception("Boom")

    with pytest.raises(ExtractionError):
        extractor._run_ytdlp_sync("https://invalid")
