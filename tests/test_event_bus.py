"""Tests for the async EventBus."""

import pytest
from core.event_bus import (
    DownloadProgressEvent,
    DownloadStateChangedEvent,
    EventBus,
)


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    received_events: list[DownloadProgressEvent] = []

    async def async_handler(evt: DownloadProgressEvent) -> None:
        received_events.append(evt)

    bus.subscribe(DownloadProgressEvent, async_handler)

    event = DownloadProgressEvent(
        download_id="dl_123",
        bytes_downloaded=50,
        total_bytes=100,
        speed_bytes_per_sec=1024.0,
        eta_seconds=5.0,
    )
    await bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].download_id == "dl_123"
    assert received_events[0].percentage == 50.0


@pytest.mark.asyncio
async def test_event_bus_unsubscribe() -> None:
    bus = EventBus()
    count = 0

    def sync_handler(_: DownloadStateChangedEvent) -> None:
        nonlocal count
        count += 1

    bus.subscribe(DownloadStateChangedEvent, sync_handler)
    await bus.publish(DownloadStateChangedEvent(download_id="1", state="STARTED"))
    assert count == 1

    bus.unsubscribe(DownloadStateChangedEvent, sync_handler)
    await bus.publish(DownloadStateChangedEvent(download_id="1", state="COMPLETED"))
    assert count == 1  # Should not increase
