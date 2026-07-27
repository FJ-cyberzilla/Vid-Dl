"""Tests for async retry decorator."""

import pytest
from sota_dl.utils.retry import async_retry, RetryConfig


@pytest.mark.asyncio
async def test_async_retry_success_first_try() -> None:
    calls = 0

    @async_retry(config=RetryConfig(retries=3, initial_delay=0.01))
    async def successful_func() -> str:
        nonlocal calls
        calls += 1
        return "success"

    result = await successful_func()
    assert result == "success"
    assert calls == 1


@pytest.mark.asyncio
async def test_async_retry_recovers_after_failures() -> None:
    calls = 0

    @async_retry(config=RetryConfig(retries=3, initial_delay=0.01))
    async def flaky_func() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("Flaky network")
        return "recovered"

    result = await flaky_func()
    assert result == "recovered"
    assert calls == 3


@pytest.mark.asyncio
async def test_async_retry_exceeds_max_retries() -> None:
    calls = 0

    @async_retry(config=RetryConfig(retries=2, initial_delay=0.01))
    async def failing_func() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("Permanent failure")

    with pytest.raises(ValueError, match="Permanent failure"):
        await failing_func()

    assert calls == 3  # 1 initial try + 2 retries


@pytest.mark.asyncio
async def test_async_retry_filters_exceptions() -> None:
    calls = 0

    @async_retry(
        config=RetryConfig(
            retries=3, initial_delay=0.01, retryable_exceptions=(TimeoutError,)
        )
    )
    async def specific_error_func() -> None:
        nonlocal calls
        calls += 1
        raise KeyError("Unretryable error")

    with pytest.raises(KeyError):
        await specific_error_func()

    assert calls == 1  # Should not retry KeyError
