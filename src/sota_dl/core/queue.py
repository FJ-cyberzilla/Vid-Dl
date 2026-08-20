"""
Core - Priority Download Queue
Provides prioritized multi-video queue management, task state tracking,
and event publishing for download execution.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Any


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


from sota_dl.core.protocols import EventBusProtocol, RepositoryProtocol

class PriorityDownloadQueue:
    """
    Async priority download queue managing multi-video states, prioritization,
    and event integration with EventBus.
    """

    def __init__(
        self, 
        event_bus: EventBusProtocol | None = None, 
        repository: RepositoryProtocol | None = None
    ) -> None:
        self._queue: asyncio.PriorityQueue[PriorityItem] = asyncio.PriorityQueue()
        self._items: dict[str, DownloadQueueItem] = {}
        self._event_bus = event_bus
        self._repository = repository
        self._lock = asyncio.Lock()
        self._load_from_repository()

    def _load_from_repository(self) -> None:
        """Loads items from the repository if provided."""
        if not self._repository:
            return
            
        for item in self._repository.load_all():
            self._items[item.item_id] = item
            self._requeue_if_pending(item)

    def _requeue_if_pending(self, item: DownloadQueueItem) -> None:
        """Helper to requeue a pending item."""
        if item.state != QueueItemState.PENDING:
            return
            
        priority_entry = PriorityItem(
            priority=item.priority,
            timestamp=item.created_at,
            item_id=item.item_id,
        )
        self._queue.put_nowait(priority_entry)

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
        """Enqueues a new URL for download with a specified priority."""
        async with self._lock:
            self._check_item_exists(item_id)
            item = self._create_queue_item(item_id, url, priority, metadata)
            self._items[item_id] = item
            self._persist_item(item)
            await self._add_to_queue(item)

        await self._notify_state_change(item_id, QueueItemState.PENDING.name)
        return item

    def _check_item_exists(self, item_id: str) -> None:
        """Raises ValueError if item already exists."""
        if item_id in self._items:
            raise ValueError(f"Download item with ID '{item_id}' already exists.")

    def _create_queue_item(
        self, item_id: str, url: str, priority: int, metadata: dict[str, str] | None
    ) -> DownloadQueueItem:
        """Creates a new DownloadQueueItem."""
        return DownloadQueueItem(
            item_id=item_id,
            url=url,
            priority=priority,
            state=QueueItemState.PENDING,
            metadata=metadata or {},
        )

    async def _add_to_queue(self, item: DownloadQueueItem) -> None:
        """Adds an item to the priority queue."""
        priority_entry = PriorityItem(
            priority=item.priority, timestamp=item.created_at, item_id=item.item_id
        )
        await self._queue.put(priority_entry)

    def _persist_item(self, item: DownloadQueueItem) -> None:
        """Persists the item to repository if available."""
        if self._repository:
            self._repository.save_item(item)

    async def dequeue(self) -> DownloadQueueItem:
        """Retrieves the next pending download item from the priority queue."""
        while True:
            priority_entry = await self._queue.get()
            item = self._items[priority_entry.item_id]

            if await self._try_process_item(item):
                return item

    async def _try_process_item(self, item: DownloadQueueItem) -> bool:
        """Attempts to transition an item to processing state."""
        async with self._lock:
            if item.state in (QueueItemState.CANCELLED, QueueItemState.PAUSED):
                self._queue.task_done()
                return False

            item.state = QueueItemState.PROCESSING
            self._persist_item(item)

        await self._notify_state_change(item.item_id, QueueItemState.PROCESSING.name)
        return True

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

            self._apply_state_update(item, state, error_message)
            self._persist_item(item)

        await self._notify_state_change(item_id, state.name, error_message or "")

    def _apply_state_update(
        self, item: DownloadQueueItem, state: QueueItemState, error_message: str | None
    ) -> None:
        """Helper to apply state and error message updates."""
        item.state = state
        if error_message:
            item.error_message = error_message

    async def cancel(self, item_id: str) -> bool:
        """Cancels a pending or processing download task."""
        async with self._lock:
            item = self._items.get(item_id)
            if not self._can_cancel(item):
                return False

            item.state = QueueItemState.CANCELLED
            self._persist_item(item)

        await self._notify_state_change(item_id, QueueItemState.CANCELLED.name)
        return True

    def _can_cancel(self, item: DownloadQueueItem | None) -> bool:
        """Checks if an item can be cancelled."""
        if not item:
            return False
        return item.state not in (QueueItemState.COMPLETED, QueueItemState.FAILED)

    async def _notify_state_change(
        self, item_id: str, state_name: str, message: str = ""
    ) -> None:
        """Notifies EventBus of a state change."""
        if not self._event_bus:
            return

        from sota_dl.core.event_bus import DownloadStateChangedEvent
        event = DownloadStateChangedEvent(
            download_id=item_id, state=state_name, error_message=message
        )
        await self._event_bus.publish(event)
