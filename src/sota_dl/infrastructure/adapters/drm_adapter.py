"""
Adapter for DRM decryption, compliant with DownloaderBackend protocol.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Union
from pathlib import Path

from sota_dl.core.protocols import DownloaderBackend, DownloadResult, DownloadStatus, DownloadOptions
from sota_dl.infrastructure.adapters.drm_factory import get_best_drm_service

logger = logging.getLogger(__name__)


class DrmBackend(DownloaderBackend):
    """Adapter to map DRM decryption services to DownloaderBackend protocol."""

    def download(
        self,
        target: str,
        options: DownloadOptions,
        progress_hook: Callable[[dict[str, Union[str, float, int]]], None],
    ) -> DownloadResult:
        """Execute a DRM-protected download."""
        if not options.device_wvd_path:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error="DRM decryption required but no device file provided.",
                metadata={"target": target},
            )

        try:
            drm_service = get_best_drm_service(options.device_wvd_path)
        except Exception as e:
            logger.error("Failed to initialize DRM service: %s", e)
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error=f"DRM service initialization failed: {e}",
                metadata={"target": target},
            )

        try:
            # Run the async decryption synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            final_path = loop.run_until_complete(
                drm_service.adecrypt(
                    url=target,
                    output_path=options.output_dir / f"{Path(target).stem}.mp4",
                    headers=options.extra_args.get("headers", {}),
                    timeout=options.timeout,
                )
            )
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                file_path=final_path,
                metadata={"target": target},
            )
        except Exception as e:
            logger.exception("DRM decryption failed for %s", target)
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error=f"DRM decryption failed: {e}",
                metadata={"target": target},
            )
