"""Base network handling with rate limiting and header management."""

import asyncio
import logging
from typing import Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Basic rate limiter
_RATE_LIMITER = asyncio.Semaphore(5)  # Max 5 concurrent requests


class NetworkClient:
    """Centralized client for network requests with rate limiting and headers."""

    def __init__(self, user_agent: str | None = None):
        self.headers = {
            "User-Agent": user_agent or "SOTA-Downloader/3.0.1",
            "Accept": "*/*",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Perform a throttled GET request."""
        async with _RATE_LIMITER:
            logger.debug("Requesting URL: %s", url)
            timeout = kwargs.pop("timeout", 10)
            headers = {**self.headers, **kwargs.pop("headers", {})}
            # Using run_in_executor because requests is blocking
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=timeout, **kwargs),
            )
