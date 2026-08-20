import asyncio
from typing import Any
from sota_dl.infrastructure.cache.cache_manager import CacheManager


class AsyncCacheAdapter:
    """Adapter to make CacheManager conform to MetadataCacheProtocol."""

    def __init__(self, cache: CacheManager):
        self._cache = cache

    async def get(self, url_key: str) -> dict[str, Any] | None:
        """Retrieves cached metadata."""
        return await asyncio.to_thread(self._cache.get, url_key)

    async def set(
        self, url_key: str, data: dict[str, Any], ttl: int | None = None
    ) -> None:
        """Stores cached metadata."""
        await asyncio.to_thread(self._cache.set, url_key, data, ttl)

    async def delete(self, url_key: str) -> bool:
        """Removes a cached entry."""
        # CacheManager doesn't support explicit deletion.
        # Returning False as it's not implemented.
        return False

    async def clear(self) -> None:
        """Clears all cached entries."""
        await asyncio.to_thread(self._cache.clear)
