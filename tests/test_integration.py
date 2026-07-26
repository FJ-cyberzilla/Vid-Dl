import pytest
from pathlib import Path
from unittest.mock import patch
from core.extractor import MediaExtractor
from infrastructure.cache import MetadataCache, CacheConfig


@pytest.mark.asyncio
async def test_end_to_end_extraction_caching(tmp_path: Path) -> None:
    """
    Integration test: Verify that the Extractor interacts correctly with
    the MetadataCache during a lifecycle event.
    """
    # 1. Setup Infrastructure
    cache_dir = tmp_path / "cache"
    cache = MetadataCache(CacheConfig(db_path=cache_dir / "meta.db"))

    # 2. Setup Core
    extractor = MediaExtractor(cache=cache)

    # 3. Execution
    url = "https://example.com/video"
    mock_info = {"id": "123", "title": "Integrity Test"}

    # Simulate extraction bypassing the network
    with patch.object(extractor, "_run_ytdlp_sync", return_value=mock_info):
        # First call: Cache miss
        info1 = await extractor.extract_info(url, force_refresh=True)
        assert info1 == mock_info

        # Second call: Cache hit (verify interaction)
        info2 = await extractor.extract_info(url, force_refresh=False)
        assert info2 == mock_info

        # Verify persistence
        cached = await cache.get(url)
        assert cached == mock_info
