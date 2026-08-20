import json
import time
import structlog
from pathlib import Path
from typing import Any

logger = structlog.get_logger(__name__)


class CacheManager:
    """Handles persistent file-based caching for tokens and video metadata."""

    def __init__(self, cache_dir: Path | None = None):
        # Store cache in user home directory (~/.cache/sota_dl)
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "sota_dl")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("CacheManager initialized", cache_dir=str(self.cache_dir))

    def _get_path(self, key: str) -> Path:
        # Sanitize key for filesystem safe name
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Any | None:
        """Retrieves item from cache if it exists and hasn't expired."""
        filepath = self._get_path(key)
        if not filepath.exists():
            logger.debug("Cache miss", key=key)
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            # Check Time-To-Live (TTL) expiry
            expires_at = data.get("expires_at")
            if expires_at and time.time() > expires_at:
                logger.debug("Cache expired", key=key)
                filepath.unlink(missing_ok=True)  # Delete expired cache
                return None

            logger.debug("Cache hit", key=key)
            return data.get("value")
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read cache", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = 3600) -> None:
        """Saves item to cache with an optional TTL (default: 1 hour)."""
        filepath = self._get_path(key)
        expires_at = (time.time() + ttl_seconds) if ttl_seconds else None

        payload = {
            "created_at": time.time(),
            "expires_at": expires_at,
            "value": value,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.debug("Cache set", key=key)
        except OSError as e:
            logger.error("Failed to write cache", key=key, error=str(e))

    def clear(self) -> None:
        """Clears all cached files."""
        logger.info("Clearing cache")
        for file in self.cache_dir.glob("*.json"):
            file.unlink(missing_ok=True)
