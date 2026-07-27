"""Tests for the async EventBus."""

import pytest
from sota_dl.core.event_bus import (
    DownloadStateChangedEvent,
    EventBus,
)


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    received_events: list[DownloadStateChangedEvent] = []

    async def async_handler(evt: DownloadStateChangedEvent) -> None:
        received_events.append(evt)

    bus.subscribe(DownloadStateChangedEvent, async_handler)

    event = DownloadStateChangedEvent(
        download_id="dl_123",
        state="STARTED",
    )
    await bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].download_id == "dl_123"
    assert received_events[0].state == "STARTED"


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
