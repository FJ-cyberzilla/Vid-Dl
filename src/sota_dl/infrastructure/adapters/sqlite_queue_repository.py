"""
Infrastructure - SQLite Queue Repository
Persists download queue state to ensure recovery across application restarts.
"""

import sqlite3
import json
from pathlib import Path
from sota_dl.core.queue import DownloadQueueItem, QueueItemState


class SQLiteQueueRepository:
    """Handles persistence of DownloadQueueItems to a SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queue_items (
                    item_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    error_message TEXT,
                    created_at REAL NOT NULL,
                    metadata TEXT
                )
                """)
            conn.commit()

    def save_item(self, item: DownloadQueueItem) -> None:
        """Persists or updates an item in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO queue_items
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_id,
                    item.url,
                    item.priority,
                    item.state.name,
                    item.error_message,
                    item.created_at,
                    json.dumps(item.metadata),
                ),
            )
            conn.commit()

    def load_all(self) -> list[DownloadQueueItem]:
        """Loads all items from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM queue_items")
            items = []
            for row in cursor.fetchall():
                items.append(
                    DownloadQueueItem(
                        item_id=row[0],
                        url=row[1],
                        priority=row[2],
                        state=QueueItemState[row[3]],
                        error_message=row[4],
                        created_at=row[5],
                        metadata=json.loads(row[6]),
                    )
                )
            return items
