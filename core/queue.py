"""
Core - Priority Download Queue
Provides prioritized multi-video queue management, task state tracking,
and event publishing for download execution.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
import time


class QueueItemState(Enum):
    """Represents the execution state of a download queue item."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    PAUSED = auto()


@dataclass(order=True)
class PriorityItem:
    """
    Wrapper for ordering items in the priority queue.
    Sort order: priority (lower number = higher priority),
    then timestamp (FIFO for ties).
    """

    priority: int
    timestamp: float = field(compare=True)
    item_id: str = field(compare=False)


@dataclass
class DownloadQueueItem:
    """Container holding metadata, state, and priority for a queued download task."""

    item_id: str
    url: str
    priority: int = 10  # Default priority (lower = higher priority)
    state: QueueItemState = QueueItemState.PENDING
    error_message: str | None = None
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, str] = field(default_factory=dict)


class PriorityDownloadQueue:
    """
    Async priority download queue managing multi-video states, prioritization,
    and event integration with EventBus.
    """

    def __init__(self, event_bus: object | None = None) -> None:
        self._queue: asyncio.PriorityQueue[PriorityItem] = asyncio.PriorityQueue()
        self._items: dict[str, DownloadQueueItem] = {}
        self._event_bus = event_bus
        self._lock = asyncio.Lock()

    @property
    def total_count(self) -> int:
        """Returns the total number of items managed by the queue."""
        return len(self._items)

    @property
    def pending_count(self) -> int:
        """Returns the number of items remaining in the pending queue."""
        return self._queue.qsize()

    def get_item(self, item_id: str) -> DownloadQueueItem | None:
        """Retrieves a queue item by its unique ID."""
        return self._items.get(item_id)

    def list_items(self) -> list[DownloadQueueItem]:
        """Returns a snapshot list of all tracked download queue items."""
        return list(self._items.values())

    async def enqueue(
        self,
        item_id: str,
        url: str,
        priority: int = 10,
        metadata: dict[str, str] | None = None,
    ) -> DownloadQueueItem:
        """
        Enqueues a new URL for download with a specified priority.
        Lower priority numbers indicate higher execution precedence.
        """
        async with self._lock:
            if item_id in self._items:
                raise ValueError(f"Download item with ID '{item_id}' already exists.")

            item = DownloadQueueItem(
                item_id=item_id,
                url=url,
                priority=priority,
                state=QueueItemState.PENDING,
                metadata=metadata or {},
            )
            self._items[item_id] = item

            priority_entry = PriorityItem(
                priority=priority, timestamp=item.created_at, item_id=item_id
            )
            await self._queue.put(priority_entry)

        await self._notify_state_change(item_id, QueueItemState.PENDING.name)
        return item

    async def dequeue(self) -> DownloadQueueItem:
        """
        Retrieves the next pending download item from the priority queue.
        Blocks until an item is available.
        """
        while True:
            priority_entry = await self._queue.get()
            item = self._items[priority_entry.item_id]

            async with self._lock:
                # Skip items that were cancelled or paused while waiting in queue
                if item.state in (QueueItemState.CANCELLED, QueueItemState.PAUSED):
                    self._queue.task_done()
                    continue

                item.state = QueueItemState.PROCESSING

            await self._notify_state_change(
                item.item_id, QueueItemState.PROCESSING.name
            )
            return item

    def task_done(self) -> None:
        """Signals that a formerly dequeued task is completed."""
        self._queue.task_done()

    async def update_state(
        self, item_id: str, state: QueueItemState, error_message: str | None = None
    ) -> None:
        """Updates the state of a specific item and publishes a state change event."""
        async with self._lock:
            item = self._items.get(item_id)
            if not item:
                return

            item.state = state
            if error_message:
                item.error_message = error_message

        await self._notify_state_change(item_id, state.name, error_message or "")

    async def cancel(self, item_id: str) -> bool:
        """Cancels a pending or processing download task."""
        async with self._lock:
            item = self._items.get(item_id)
            if not item or item.state in (
                QueueItemState.COMPLETED,
                QueueItemState.FAILED,
            ):
                return False

            item.state = QueueItemState.CANCELLED

        await self._notify_state_change(item_id, QueueItemState.CANCELLED.name)
        return True

    async def _notify_state_change(
        self, item_id: str, state_name: str, message: str = ""
    ) -> None:
        if self._event_bus and hasattr(self._event_bus, "publish"):
            from core.event_bus import DownloadStateChangedEvent  # pylint: disable=import-outside-toplevel

            event = DownloadStateChangedEvent(
                download_id=item_id, state=state_name, error_message=message
            )
            await self._event_bus.publish(event)
