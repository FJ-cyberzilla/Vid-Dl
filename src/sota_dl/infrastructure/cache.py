"""
Infrastructure - Metadata TTL Cache
Provides a persistent SQLite-backed metadata cache with Time-To-Live (TTL) expiration.
"""

import asyncio
import contextlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from collections.abc import Generator


@dataclass(slots=True, frozen=True)
class CacheConfig:
    """Configuration options for SQLite metadata TTL cache."""

    db_path: Path = Path(".cache/metadata.db")
    default_ttl: int = 86400  # Default 24 hours in seconds
    max_entries: int = 1000  # Maximum records before triggering cleanup


class MetadataCache:
    """
    Persistent SQLite-backed TTL cache for yt-dlp metadata extraction.
    Thread-safe and async-friendly.
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        self.config = config or CacheConfig()
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(str(self.config.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    @contextlib.contextmanager
    def _managed_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager to ensure connection is properly closed."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes the database schema and indices if they do not exist."""
        with self._managed_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    url_key TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires_at "
                "ON metadata_cache(expires_at)"
            )

    async def get(self, url_key: str) -> dict[str, Any] | None:
        """
        Retrieves cached metadata for a given URL key if present and unexpired.
        """
        return await asyncio.to_thread(self._get_sync, url_key)

    def _get_sync(self, url_key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._managed_connection() as conn:
            cursor = conn.execute(
                "SELECT data_json, expires_at FROM metadata_cache WHERE url_key = ?",
                (url_key,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            expires_at = float(row["expires_at"])
            if now > expires_at:
                # Evict expired record on read
                conn.execute("DELETE FROM metadata_cache WHERE url_key = ?", (url_key,))
                return None

            try:
                data = json.loads(row["data_json"])
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
                return None
            except json.JSONDecodeError:
                return None

    async def set(
        self, url_key: str, data: dict[str, Any], ttl: int | None = None
    ) -> None:
        """
        Stores metadata in the cache with a specified or default TTL in seconds.
        """
        await asyncio.to_thread(self._set_sync, url_key, data, ttl)

    def _set_sync(
        self, url_key: str, data: dict[str, Any], ttl: int | None = None
    ) -> None:
        now = time.time()
        effective_ttl = ttl if ttl is not None else self.config.default_ttl
        expires_at = now + effective_ttl
        data_json = json.dumps(data)

        with self._managed_connection() as conn:
            conn.execute(
                """
                INSERT INTO metadata_cache (url_key, data_json, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url_key) DO UPDATE SET
                    data_json = excluded.data_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (url_key, data_json, now, expires_at),
            )

        # Trigger background eviction if exceeding max entries
        self._prune_sync()

    async def delete(self, url_key: str) -> bool:
        """Removes an entry explicitly from the cache."""
        return await asyncio.to_thread(self._delete_sync, url_key)

    def _delete_sync(self, url_key: str) -> bool:
        with self._managed_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM metadata_cache WHERE url_key = ?", (url_key,)
            )
            return cursor.rowcount > 0

    async def clear(self) -> None:
        """Clears all cached metadata entries."""
        await asyncio.to_thread(self._clear_sync)

    def _clear_sync(self) -> None:
        with self._managed_connection() as conn:
            conn.execute("DELETE FROM metadata_cache")

    def _prune_sync(self) -> None:
        """Prunes expired entries and enforces max_entries capacity limits."""
        now = time.time()
        with self._managed_connection() as conn:
            # Delete expired entries
            conn.execute("DELETE FROM metadata_cache WHERE expires_at < ?", (now,))

            # Enforce max entries cap (LRU/FIFO eviction)
            cursor = conn.execute("SELECT COUNT(*) as count FROM metadata_cache")
            count = cursor.fetchone()["count"]

            if count > self.config.max_entries:
                overflow = count - self.config.max_entries
                conn.execute(
                    """
                    DELETE FROM metadata_cache WHERE url_key IN (
                        SELECT url_key FROM metadata_cache
                        ORDER BY created_at ASC LIMIT ?
                    )
                    """,
                    (overflow,),
                )
