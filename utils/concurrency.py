"""
Utils - Concurrency & Async Execution
Provides bounded concurrency mechanisms, task groups, and worker pools.
"""

import asyncio
from dataclasses import dataclass
from typing import (
    Generic,
    TypeVar,
)
from collections.abc import AsyncIterable, Awaitable, Callable

T = TypeVar("T")
R = TypeVar("R")


@dataclass(slots=True)
class TaskResult(Generic[T, R]):
    """Represents the outcome of a bounded task execution."""

    item: T
    result: R | None = None
    exception: BaseException | None = None

    @property
    def is_success(self) -> bool:
        """Returns True if the task completed without an exception."""
        return self.exception is None


class BoundedExecutor:
    """
    Executes an async function across a collection of items with a fixed limit
    on concurrent executions.
    """

    def __init__(self, max_concurrency: int = 4) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def map(
        self,
        func: Callable[[T], Awaitable[R]],
        items: list[T],
        on_progress: Callable[[TaskResult[T, R]], Awaitable[None] | None] | None = None,
        return_exceptions: bool = True,
    ) -> list[TaskResult[T, R]]:
        """
        Executes func(item) for each item in parallel, throttled by max_concurrency.
        """
        results: list[TaskResult[T, R]] = []

        async def _worker(item: T) -> TaskResult[T, R]:
            async with self._semaphore:
                try:
                    res = await func(item)
                    task_res = TaskResult(item=item, result=res)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    if not return_exceptions:
                        raise
                    task_res = TaskResult(item=item, exception=exc)

                if on_progress:
                    callback_res = on_progress(task_res)
                    if asyncio.iscoroutine(callback_res):
                        await callback_res

                return task_res

        tasks = [asyncio.create_task(_worker(item)) for item in items]
        if tasks:
            results = list(await asyncio.gather(*tasks, return_exceptions=False))

        return results

    async def execute_single(
        self, func: Callable[[T], Awaitable[R]], item: T
    ) -> TaskResult[T, R]:
        """Convenience method to execute a single task within the bounded semaphore."""
        res = await self.map(func, [item], return_exceptions=True)
        return res[0]


class AsyncWorkerPool(Generic[T, R]):
    """
    A producer-consumer worker pool for continuous queue processing.
    Ideal for multi-item/playlist video downloads.
    """

    def __init__(
        self,
        worker_func: Callable[[T], Awaitable[R]],
        num_workers: int = 4,
        max_queue_size: int = 0,
    ) -> None:
        self.worker_func = worker_func
        self.num_workers = num_workers
        self._queue: asyncio.Queue[T | None] = asyncio.Queue(maxsize=max_queue_size)
        self._results: asyncio.Queue[TaskResult[T, R]] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    async def start(self) -> None:
        """Starts the worker pool tasks."""
        if self._running:
            return
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker_loop()) for _ in range(self.num_workers)
        ]

    async def _worker_loop(self) -> None:
        while True:
            item = await self._queue.get()
            if item is None:
                self._queue.task_done()
                break

            try:
                res = await self.worker_func(item)
                await self._results.put(TaskResult(item=item, result=res))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                await self._results.put(TaskResult(item=item, exception=exc))
            finally:
                self._queue.task_done()

    async def put(self, item: T) -> None:
        """Enqueues an item for processing."""
        await self._queue.put(item)

    async def join(self) -> None:
        """Waits until all queued items have been processed."""
        await self._queue.join()

    async def shutdown(self) -> None:
        """Gracefully stops all workers in the pool."""
        if not self._running:
            return

        for _ in range(self.num_workers):
            await self._queue.put(None)

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._running = False

    async def results(self) -> AsyncIterable[TaskResult[T, R]]:
        """Yields completed task results as they become available."""
        while not self._results.empty():
            yield await self._results.get()
