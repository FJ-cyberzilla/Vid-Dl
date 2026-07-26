"""
Adapter to make YtDlpEngine compliant with DownloaderBackend protocol.
"""

from collections.abc import Callable
from typing import Any
from core.protocols import DownloadOptions, DownloadResult, DownloadStatus
from infrastructure.yt_dlp_wrapper import YtDlpEngine, YtDlpError
import logging

logger = logging.getLogger(__name__)


class YtDlpBackend:
    """Adapter to map YtDlpEngine to DownloaderBackend protocol."""

    def __init__(self) -> None:
        self.engine = YtDlpEngine()

    def download(
        self,
        target: str,
        options: DownloadOptions,
        progress_hook: Callable[[dict[str, Any]], Any],
    ) -> DownloadResult:
        """Execute a download."""

        # Mapping DownloadOptions to engine opts
        extra_opts = options.extra_args.copy()
        if options.cookiefile:
            extra_opts["cookiefile"] = str(options.cookiefile)

        try:
            file_path = self.engine.download(
                target,
                options.output_dir,
                progress_callback=progress_hook,
                extra_opts=extra_opts,
            )
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                file_path=file_path,
                metadata={"target": target},
            )
        except YtDlpError as e:
            logger.exception("Download failed for %s", target)
            return DownloadResult(
                status=DownloadStatus.FAILED, error=str(e), metadata={"target": target}
            )
