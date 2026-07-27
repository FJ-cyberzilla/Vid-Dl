"""Tests for PriorityDownloadQueue."""

import pytest
from sota_dl.core.event_bus import DownloadStateChangedEvent, EventBus
from sota_dl.core.queue import PriorityDownloadQueue, QueueItemState


@pytest.mark.asyncio
async def test_priority_queue_ordering() -> None:
    queue = PriorityDownloadQueue()

    # Enqueue low priority item first, then high priority item
    await queue.enqueue(item_id="video_low", url="https://example.com/2", priority=20)
    await queue.enqueue(item_id="video_high", url="https://example.com/1", priority=1)

    assert queue.pending_count == 2

    # High priority should be dequeued first
    first = await queue.dequeue()
    assert first.item_id == "video_high"
    assert first.state == QueueItemState.PROCESSING
    queue.task_done()

    second = await queue.dequeue()
    assert second.item_id == "video_low"
    queue.task_done()


@pytest.mark.asyncio
async def test_queue_event_bus_integration() -> None:
    event_bus = EventBus()
    received_events: list[DownloadStateChangedEvent] = []

    async def handler(evt: DownloadStateChangedEvent) -> None:
        received_events.append(evt)

    event_bus.subscribe(DownloadStateChangedEvent, handler)

    queue = PriorityDownloadQueue(event_bus=event_bus)
    await queue.enqueue(item_id="item_1", url="https://example.com/test", priority=5)

    assert len(received_events) == 1
    assert received_events[0].download_id == "item_1"
    assert received_events[0].state == "PENDING"

    await queue.update_state("item_1", QueueItemState.COMPLETED)
    assert len(received_events) == 2
    assert received_events[1].state == "COMPLETED"
