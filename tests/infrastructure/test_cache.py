"""Tests for MetadataCache."""

import asyncio
import pytest
from pathlib import Path
from sota_dl.infrastructure.cache import CacheConfig, MetadataCache


@pytest.mark.asyncio
async def test_cache_set_and_get(tmp_path: Path) -> None:
    config = CacheConfig(db_path=tmp_path / "test_cache.db", default_ttl=60)
    cache = MetadataCache(config)

    test_data = {"id": "v123", "title": "Test Video", "duration": 180}
    await cache.set("https://example.com/video", test_data)

    retrieved = await cache.get("https://example.com/video")
    assert retrieved == test_data


@pytest.mark.asyncio
async def test_cache_ttl_expiration(tmp_path: Path) -> None:
    config = CacheConfig(db_path=tmp_path / "test_cache.db", default_ttl=1)
    cache = MetadataCache(config)

    await cache.set("https://example.com/expired", {"title": "Expired"}, ttl=1)
    await asyncio.sleep(1.1)  # Wait for TTL expiration

    retrieved = await cache.get("https://example.com/expired")
    assert retrieved is None
