"""DRM decryption service using pywidevine and video_download_drm."""

from __future__ import annotations

import asyncio
import concurrent.futures
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

# -------------------------------------------------------------------------
# Lazy imports – we only load these when the class is actually used.
# This keeps your app startup fast and avoids missing-dependency crashes.
# -------------------------------------------------------------------------
_pywidevine_available = False
_video_download_drm_available = False

try:
    from pywidevine.device import Device as _Device
    from pywidevine.cdm import Cdm as _Cdm

    # Verify essential API is present (guard against future changes)
    if not hasattr(_Device, "load") or not hasattr(_Cdm, "from_device"):
        raise ImportError("pywidevine API mismatch")
    _pywidevine_available = True
except ImportError:
    _Device = None
    _Cdm = None

try:
    from video_download_drm import DrmDownloader as _DrmDownloader

    if not hasattr(_DrmDownloader, "run"):
        raise ImportError("video_download_drm API mismatch")
    _video_download_drm_available = True
except ImportError:
    _DrmDownloader = None


class DRMError(Exception):
    """Raised when DRM decryption fails."""


class DependencyMissingError(DRMError):
    """Raised when required DRM packages are not installed."""

    def __init__(self) -> None:
        super().__init__(
            "DRM support requires 'pywidevine' and 'video_download_drm'.\n"
            "Install with: pip install pywidevine video-download-drm"
        )


# -------------------------------------------------------------------------
# Abstract base for future DRM implementations
# -------------------------------------------------------------------------
class DRMService(ABC):
    """Abstract interface for DRM decryption services."""

    @abstractmethod
    def decrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """Download and decrypt a DRM‑protected video synchronously."""

    @abstractmethod
    async def adecrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """Download and decrypt a DRM‑protected video asynchronously."""


class WidevineDRM(DRMService):
    """
    Handles Widevine L3 DRM decryption using a device file (.wvd).

    Usage:
        drm = WidevineDRM(device_wvd_path=Path("/path/to/device.wvd"))
        output = drm.decrypt(
            url="https://example.com/manifest.mpd",
            output_path=Path("./video.mp4"),
            headers={"User-Agent": "..."},
            progress_callback=lambda p: print(f"Progress: {p:.1f}%")
        )
    """

    # Dedicated thread pool to avoid clogging the default executor
    _executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=5, thread_name_prefix="drm_worker"
    )

    def __init__(self, device_wvd_path: Path):
        """
        Args:
            device_wvd_path: Path to the Widevine device file (e.g., device.wvd).
        """
        if not _pywidevine_available or not _video_download_drm_available:
            raise DependencyMissingError()

        if not device_wvd_path.exists():
            raise DRMError(f"Device file not found: {device_wvd_path}")

        self.device_wvd_path = device_wvd_path
        self._device = None
        self._cdm = None

    @property
    def device(self) -> Any:
        """Lazy-load the Widevine Device object from the .wvd file."""
        if self._device is None:
            self._device = _Device.load(str(self.device_wvd_path))
        return self._device

    @property
    def cdm(self) -> Any:
        """Lazy-load a Cdm instance bound to the loaded Device."""
        if self._cdm is None:
            self._cdm = _Cdm.from_device(self.device)
        return self._cdm

    def _run_with_timeout(self, run_func: Callable[[], Any], timeout: float) -> None:
        """Helper to run a function in a thread pool with a timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_func)
            try:
                future.result(timeout=timeout)
            except concurrent.futures.TimeoutError as e:
                raise DRMError(
                    f"DRM decryption timed out after {timeout} seconds"
                ) from e

    def _run_download(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str],
        progress_callback: Callable[[float], None] | None,
        timeout: float | None,
    ) -> None:
        """Blocking helper that runs the DrmDownloader, optionally with a timeout."""
        downloader = _DrmDownloader(
            url=url,
            output=str(output_path),
            cdm=self.cdm,
            headers=headers,
        )

        if progress_callback:
            progress_callback(0.0)

        try:
            if timeout is not None:
                self._run_with_timeout(downloader.run, timeout)
            else:
                downloader.run()
        except (OSError, KeyError, AttributeError, ValueError) as e:
            raise DRMError(f"DRM decryption failed: {e}") from e
        finally:
            if progress_callback:
                progress_callback(100.0)

    def _validate_url(self, url: str) -> None:
        """Validate the manifest URL."""
        if not isinstance(url, str) or not url.strip():
            raise DRMError("URL must be a non‑empty string")
        if not url.startswith(("http://", "https://")):
            raise DRMError("URL must start with http:// or https://")

    def decrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """
        Download and decrypt a DRM‑protected video.

        Args:
            url: Manifest URL (.mpd or .m3u8). Must be a valid HTTP(S) URL.
            output_path: Where to save the final decrypted MP4.
            headers: Additional HTTP headers (cookies, auth tokens, etc.).
            progress_callback: Called with a float percentage (0-100) at start
                and end of decryption. (Library does not support real‑time progress.)
            timeout: Maximum number of seconds to wait for decryption.
                ``None`` means no timeout.

        Returns:
            Path to the decrypted video file.

        Raises:
            DRMError: If decryption fails or times out.
        """
        # Validate URL
        self._validate_url(url)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._run_download(
            url=url,
            output_path=output_path,
            headers=headers or {},
            progress_callback=progress_callback,
            timeout=timeout,
        )

        # Verify output exists
        if not output_path.exists():
            raise DRMError("Decryption completed but output file not found.")

        return output_path

    async def adecrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """
        Async version of decrypt() – runs the blocking operation in a
        dedicated thread pool. Supports cancellation and optional timeout
        via `asyncio.wait_for`.
        """
        loop = asyncio.get_running_loop()
        # Run the blocking method in our own executor to avoid clogging the default pool
        coro = loop.run_in_executor(
            self._executor,
            self.decrypt,
            url,
            output_path,
            headers,
            progress_callback,
            timeout,
        )
        if timeout is not None:
            try:
                return await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                raise DRMError(
                    f"DRM decryption timed out after {timeout} seconds"
                ) from None
        else:
            return await coro

    @classmethod
    def shutdown_executor(cls, wait: bool = True) -> None:
        """Cleanly shut down the shared thread pool (optional)."""
        cls._executor.shutdown(wait=wait)


# -------------------------------------------------------------------------
# Convenience factory function – useful for dependency checking
# -------------------------------------------------------------------------
def create_drm_service(device_path: Path) -> DRMService | None:
    """
    Factory that returns a DRMService instance if dependencies are met,
    otherwise returns None (so your app can gracefully degrade).
    """
    try:
        return WidevineDRM(device_path)
    except DependencyMissingError:
        return None
