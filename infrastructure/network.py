"""Production‑ready network utilities with async support, speed tests, and retries."""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class NetworkError(Exception):
    """Base exception for network operations."""


class InvalidURLError(NetworkError):
    """The URL is malformed."""


class SpeedMeasurementError(NetworkError):
    """Could not measure network speed."""


# ---------------------------------------------------------------------------
# Network Manager
# ---------------------------------------------------------------------------
class NetworkManager:
    """
    A robust, async‑compatible network manager.

    Features:
        - Persistent session with connection pooling
        - Automatic retries with backoff
        - Proxy support
        - URL validation and reachability checks
        - Real download speed measurement
        - Both sync and async interfaces

    Usage::

        nm = NetworkManager()
        if nm.check_url("https://example.com/file.bin"):
            speed = nm.get_speed_mbps()
        await nm.check_url_async("https://...")
    """

    # Lightweight test file for speed measurement (1 MB – CDN backed)
    SPEED_TEST_URL = "https://speed.hetzner.de/1MB.bin"
    # Default measurement duration (seconds)
    SPEED_TEST_DURATION = 3.0
    # Default chunk size for downloads (bytes)
    CHUNK_SIZE = 65536  # 64 KiB

    def __init__(
        self,
        proxy: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        user_agent: str = "NetworkManager/3.0",
    ) -> None:
        """
        Args:
            proxy: HTTP/HTTPS proxy URL (e.g., ``"http://127.0.0.1:8080"``).
            timeout: Request timeout in seconds (connect + read).
            max_retries: Maximum retries for transient failures.
            user_agent: User‑Agent header to use in all requests.
        """
        self.timeout = timeout
        self.session = self._build_session(
            proxy=proxy, max_retries=max_retries, user_agent=user_agent
        )

    @staticmethod
    def _build_session(
        proxy: str | None,
        max_retries: int,
        user_agent: str,
    ) -> requests.Session:
        """Create a requests.Session with retry strategy and optional proxy."""
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

        # Retry configuration
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
        return session

    # ------------------------------------------------------------------
    # URL validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_url(url: str) -> None:
        """Raise InvalidURLError if *url* is not plausible."""
        if not isinstance(url, str) or not url.strip():
            raise InvalidURLError("URL must be a non‑empty string.")
        if not url.startswith(("http://", "https://")):
            raise InvalidURLError("URL must start with http:// or https://")

    # ------------------------------------------------------------------
    # URL reachability check
    # ------------------------------------------------------------------
    def check_url(self, url: str) -> bool:
        """
        Synchronously check if *url* is reachable (HEAD request).

        Returns:
            ``True`` if the response status code is < 400, otherwise ``False``.
            Invalid URLs or network errors also return ``False``.
        """
        try:
            self._validate_url(url)
        except InvalidURLError:
            return False

        try:
            resp = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )
            return resp.status_code < 400
        except RequestException:
            logger.debug("HEAD request failed for %s", url, exc_info=True)
            return False

    async def check_url_async(self, url: str) -> bool:
        """
        Async wrapper around :meth:`check_url` (runs in a thread pool).
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.check_url, url)

    # ------------------------------------------------------------------
    # Speed measurement
    # ------------------------------------------------------------------
    def get_speed_mbps(
        self,
        test_url: str | None = None,
        duration: float | None = None,
        chunk_size: int | None = None,
        progress_callback: Callable[[float], Any] | None = None,
    ) -> float:
        """
        Measure download speed by fetching a known file.

        Downloads from *test_url* for up to *duration* seconds, then
        calculates the throughput in megabits per second (Mbps).

        Args:
            test_url: URL of a reliable small file (defaults to a 1 MB file).
            duration: How long to measure (seconds). ``None`` uses the class default.
            chunk_size: Bytes per read iteration.
            progress_callback: Called with Mbps snapshots during measurement.

        Returns:
            Speed in Mbps (float).

        Raises:
            SpeedMeasurementError: If the measurement fails.
        """
        test_url = test_url or self.SPEED_TEST_URL
        duration = duration or self.SPEED_TEST_DURATION
        chunk_size = chunk_size or self.CHUNK_SIZE

        start_time = time.monotonic()
        downloaded_bytes = 0

        try:
            with self.session.get(test_url, stream=True, timeout=self.timeout) as resp:
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    downloaded_bytes += len(chunk)
                    elapsed = time.monotonic() - start_time
                    # Compute current speed
                    speed_mbps = (downloaded_bytes * 8) / (elapsed * 1_000_000)
                    if progress_callback:
                        progress_callback(speed_mbps)
                    # Stop after the specified duration
                    if elapsed >= duration:
                        break
        except RequestException as exc:
            raise SpeedMeasurementError(
                f"Speed test failed: {exc}"
            ) from exc

        elapsed_total = time.monotonic() - start_time
        if elapsed_total <= 0:
            raise SpeedMeasurementError("Measurement duration too short.")

        speed_mbps = (downloaded_bytes * 8) / (elapsed_total * 1_000_000)
        logger.debug("Measured speed: %.2f Mbps", speed_mbps)
        return speed_mbps

    async def get_speed_mbps_async(
        self,
        test_url: str | None = None,
        duration: float | None = None,
        chunk_size: int | None = None,
        progress_callback: Callable[[float], Any] | None = None,
    ) -> float:
        """
        Async version of :meth:`get_speed_mbps`.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.get_speed_mbps,
            test_url,
            duration,
            chunk_size,
            progress_callback,
        )

    # ------------------------------------------------------------------
    # Resource cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying requests session."""
        self.session.close()

    def __enter__(self) -> NetworkManager:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
