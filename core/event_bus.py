"""
Core - Async Event Bus
Provides a lightweight publish-subscribe mechanism for decoupling core operations
from UI updates.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar, cast

E = TypeVar("E", bound="Event")


@dataclass(slots=True, frozen=True)
class Event:
    """Base class for all internal events."""


EventHandler = Callable[[Event], Awaitable[None] | None]


@dataclass(slots=True, frozen=True)
class DownloadProgressEvent(Event):
    """Event emitted when download progress updates."""

    download_id: str
    bytes_downloaded: int
    total_bytes: int
    speed_bytes_per_sec: float
    eta_seconds: float

    @property
    def percentage(self) -> float:
        """Calculates completion percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_downloaded / self.total_bytes) * 100


@dataclass(slots=True, frozen=True)
class DownloadStateChangedEvent(Event):
    """
    Event emitted when a download's state changes
    (e.g., STARTED, COMPLETED, FAILED).
    """

    download_id: str
    state: str
    error_message: str | None = None


class EventBus:
    """
    Central async event dispatcher for decoupling core events
    from subscriber callbacks.
    """

    def __init__(self) -> None:
        self._subscribers: dict[type[Event], list[EventHandler]] = {}

    def subscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], Awaitable[None] | None],
    ) -> None:
        """Subscribes a synchronous or asynchronous handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(cast(EventHandler, handler))

    def unsubscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], Awaitable[None] | None],
    ) -> None:
        """Unsubscribes a handler from a specific event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publishes an event to all registered handlers concurrently."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        async_tasks: list[Awaitable[None]] = []

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result) or isinstance(result, asyncio.Future):
                    async_tasks.append(result)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                _ = exc  # Logged via infrastructure logger in subscriber scope

        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)
