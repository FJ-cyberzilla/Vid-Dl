"""Tests for concurrency utilities."""

import asyncio
import pytest
from sota_dl.utils.concurrency import AsyncWorkerPool, BoundedExecutor


@pytest.mark.asyncio
async def test_bounded_executor_limit_and_order() -> None:
    executor = BoundedExecutor(max_concurrency=2)
    active_count = 0
    max_active = 0

    async def task(x: int) -> int:
        nonlocal active_count, max_active
        active_count += 1
        max_active = max(max_active, active_count)
        await asyncio.sleep(0.01)
        active_count -= 1
        return x * 2

    items = [1, 2, 3, 4, 5]
    results = await executor.map(task, items)

    assert max_active <= 2
    assert len(results) == 5
    assert [r.result for r in results] == [2, 4, 6, 8, 10]
    assert all(r.is_success for r in results)


@pytest.mark.asyncio
async def test_bounded_executor_exception_handling() -> None:
    executor = BoundedExecutor(max_concurrency=2)

    async def faulty_task(x: int) -> int:
        if x == 3:
            raise ValueError("Failed on 3")
        return x

    results = await executor.map(faulty_task, [1, 2, 3, 4])

    assert results[0].is_success and results[0].result == 1
    assert not results[2].is_success
    assert isinstance(results[2].exception, ValueError)


@pytest.mark.asyncio
async def test_async_worker_pool_lifecycle() -> None:
    processed = []

    async def worker(item: str) -> str:
        processed.append(item)
        return item.upper()

    pool = AsyncWorkerPool(worker_func=worker, num_workers=2)
    await pool.start()

    await pool.put("video1")
    await pool.put("video2")
    await pool.join()
    await pool.shutdown()

    assert len(processed) == 2
    results = [r async for r in pool.results()]
    assert len(results) == 2
    assert {r.result for r in results} == {"VIDEO1", "VIDEO2"}
