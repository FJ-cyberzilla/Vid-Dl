"""
Utils - Async Retry Mechanism
Provides async exponential backoff with randomized jitter and custom
exception filtering.
"""

import asyncio
import functools
import secrets
from dataclasses import dataclass, field
from typing import (
    Any,
    TypeVar,
)
from collections.abc import Awaitable, Callable

T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class RetryConfig:
    """Configuration options for exponential backoff retry behavior."""

    retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[BaseException], ...] = field(
        default_factory=lambda: (Exception,)
    )


def async_retry(
    config: RetryConfig | None = None,
    *,
    on_retry: Callable[[BaseException, int, float], Awaitable[None] | None]
    | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for retrying async functions using exponential backoff with jitter.

    :param config: RetryConfig instance containing backoff limits and exception rules.
    :param on_retry: Optional callback function triggered on each retry attempt.
    """
    cfg = config or RetryConfig()

    if cfg.retries < 0:
        raise ValueError("retries must be non-negative")
    if cfg.initial_delay <= 0:
        raise ValueError("initial_delay must be positive")
    if cfg.backoff_factor < 1.0:
        raise ValueError("backoff_factor must be >= 1.0")

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = cfg.initial_delay
            attempt = 0

            while True:
                try:
                    return await func(*args, **kwargs)
                except cfg.retryable_exceptions as exc:  # pylint: disable=catching-non-exception
                    attempt += 1
                    if attempt > cfg.retries:
                        raise

                    # Calculate exponential delay capped by max_delay
                    delay = min(current_delay, cfg.max_delay)

                    # Full jitter algorithm: uniform random between 0 and
                    # calculated delay
                    sleep_time = (
                        secrets.SystemRandom().uniform(0, delay)
                        if cfg.jitter
                        else delay
                    )
                    if on_retry:
                        cb_result = on_retry(exc, attempt, sleep_time)
                        if asyncio.iscoroutine(cb_result):
                            await cb_result

                    await asyncio.sleep(sleep_time)

                    # Compute next backoff step
                    current_delay = min(
                        current_delay * cfg.backoff_factor, cfg.max_delay
                    )

        return wrapper

    return decorator
