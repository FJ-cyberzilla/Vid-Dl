"""Tests for CacheManager."""

import asyncio
import pytest
from pathlib import Path
from sota_dl.infrastructure.cache.cache_manager import CacheManager


@pytest.mark.asyncio
async def test_cache_set_and_get(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")

    test_data = {"id": "v123", "title": "Test Video", "duration": 180}
    cache.set("https://example.com/video", test_data)

    retrieved = cache.get("https://example.com/video")
    assert retrieved == test_data


@pytest.mark.asyncio
async def test_cache_ttl_expiration(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")

    # CacheManager doesn't support explicit TTL per item, it sets a default in set().
    # For testing, we rely on the default or passing it.
    cache.set("https://example.com/expired", {"title": "Expired"}, ttl_seconds=1)
    await asyncio.sleep(1.1)  # Wait for TTL expiration

    retrieved = cache.get("https://example.com/expired")
    assert retrieved is None
