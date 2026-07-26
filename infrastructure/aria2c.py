"""State‑of‑the‑art aria2c external downloader with async, progress, and retries."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class Aria2cError(Exception):
    """Base exception for aria2c failures."""


class Aria2cNotFoundError(Aria2cError):
    """The aria2c binary is not installed or not found."""


class Aria2cProcessError(Aria2cError):
    """aria2c returned a non‑zero exit code."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class Aria2cTimeoutError(Aria2cError):
    """The download timed out."""


# ---------------------------------------------------------------------------
# Progress parser
# ---------------------------------------------------------------------------
_ARIA2_PROGRESS_RE = re.compile(r"\((\d+)%\)")  # e.g., "(25%)"


def _parse_progress(line: str) -> float | None:
    """Extract download percentage from an aria2c status line."""
    match = _ARIA2_PROGRESS_RE.search(line)
    if match:
        return float(match.group(1))
    return None


# ---------------------------------------------------------------------------
# Options container
# ---------------------------------------------------------------------------
@dataclass
class Aria2cOptions:
    """Configuration for a single download.

    Attributes:
        max_connections: Number of parallel connections (default 16).
        chunk_size: Chunk size passed to aria2c, e.g., ``"1M"``.
        timeout: Maximum time in seconds to wait for the download.
        retries: Number of retries on transient failures.
        progress_callback: Called with a percentage (0‑100) as download advances.
        headers: Extra HTTP headers as a dict.
    """

    max_connections: int = 16
    chunk_size: str = "1M"
    timeout: float | None = None
    retries: int = 3
    progress_callback: Callable[[float], Any] | None = None
    headers: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# Aria2c client
# ---------------------------------------------------------------------------
class Aria2cClient:
    """
    A robust, async‑ready wrapper around the aria2c command‑line downloader.

    Usage::

        client = Aria2cClient()
        path = await client.download(
            "https://example.com/file.bin",
            Path("./downloads/file.bin"),
            options=Aria2cOptions(progress_callback=lambda p: print(f"{p:.0f}%"))
        )
        # Sync:
        path = client.download_sync(url, output_path)
    """

    def __init__(self, default_timeout: float | None = None) -> None:
        """
        Args:
            default_timeout: Default timeout applied to every download if not
                overridden in *options*.
        """
        self.default_timeout = default_timeout

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_url(url: str) -> None:
        """Raise Aria2cError if the URL is invalid."""
        if not isinstance(url, str) or not url.strip():
            raise Aria2cError("URL must be a non‑empty string.")
        if not url.startswith(("http://", "https://")):
            raise Aria2cError("URL must start with http:// or https://")

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        """Create parent directories of *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)

    async def _check_binary(self) -> None:
        """Verify that aria2c is callable."""
        if shutil.which("aria2c") is None:
            raise Aria2cNotFoundError(
                "aria2c not found. Install it: https://aria2.github.io"
            )

    # ------------------------------------------------------------------
    # Command builder
    # ------------------------------------------------------------------
    @staticmethod
    def _build_command(
        url: str,
        output_path: Path,
        options: Aria2cOptions,
    ) -> list[str]:
        """Build the aria2c command line."""
        cmd = [
            "aria2c",
            "--summary-interval=0",  # suppress periodic summary
            "--console-log-level=notice",  # show progress on stderr
            f"--max-connection-per-server={options.max_connections}",
            f"--min-split-size={options.chunk_size}",
            f"--out={output_path.name}",
            url,
        ]
        if options.headers:
            for k, v in options.headers.items():
                cmd.extend(["--header", f"{k}: {v}"])
        return cmd

    # ------------------------------------------------------------------
    # Core async download
    # ------------------------------------------------------------------
    async def _run_aria2c(
        self,
        args: list[str],
        options: Aria2cOptions,
        cwd: Path,
    ) -> None:
        """
        Execute aria2c asynchronously, parse progress, handle timeout/retries.
        """
        timeout = (
            options.timeout if options.timeout is not None else self.default_timeout
        )

        for attempt in range(1, options.retries + 1):
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
            )
            try:
                # Bind `proc` as default argument to avoid B023
                async def read_stderr(
                    proc: asyncio.subprocess.Process = proc,
                ) -> str:
                    stderr_lines = []
                    if proc.stderr:
                        while True:
                            line_bytes = await proc.stderr.readline()
                            if not line_bytes:
                                break
                            line = line_bytes.decode("utf-8", errors="replace").rstrip()
                            stderr_lines.append(line)
                            if options.progress_callback:
                                pct = _parse_progress(line)
                                if pct is not None:
                                    await asyncio.get_event_loop().run_in_executor(
                                        None, options.progress_callback, pct
                                    )
                    return "\n".join(stderr_lines)

                read_task = asyncio.create_task(read_stderr())
                try:
                    if timeout is not None:
                        await asyncio.wait_for(proc.wait(), timeout=timeout)
                    else:
                        await proc.wait()
                except asyncio.TimeoutError as exc:
                    proc.kill()
                    await proc.wait()  # clean up
                    raise Aria2cTimeoutError(
                        f"Download timed out after {timeout} seconds."
                    ) from exc

                stderr = await read_task

                if proc.returncode != 0:
                    raise Aria2cProcessError(
                        f"aria2c exited with code {proc.returncode}",
                        stderr=stderr,
                    )
                logger.debug("aria2c succeeded:\n%s", stderr)
                return  # success

            except OSError as exc:
                # Transient system‑level error – retry
                logger.warning("Attempt %d failed: %s", attempt, exc)
                if attempt == options.retries:
                    raise Aria2cError(
                        f"Download failed after {options.retries} attempts"
                    ) from exc
                await asyncio.sleep(1.5 ** (attempt - 1))  # exponential backoff
            finally:
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
        raise Aria2cError("Retry loop exited unexpectedly.")

    async def download(
        self,
        url: str,
        output_path: Path,
        options: Aria2cOptions | None = None,
    ) -> Path:
        """
        Download a file using aria2c asynchronously.

        Args:
            url: The HTTP(S) URL to download.
            output_path: Full path where the file will be saved (parent dirs created).
            options: Optional :class:`Aria2cOptions` to fine‑tune behaviour.

        Returns:
            The *output_path* where the file was written.

        Raises:
            Aria2cNotFoundError: aria2c binary missing.
            Aria2cTimeoutError: Download exceeded timeout.
            Aria2cProcessError: aria2c returned an error.
            Aria2cError: Other failures.
        """
        if options is None:
            options = Aria2cOptions()

        self._validate_url(url)
        self._ensure_dir(output_path)
        await self._check_binary()

        args = self._build_command(url, output_path, options)
        await self._run_aria2c(args, options, output_path.parent)
        return output_path

    # ------------------------------------------------------------------
    # Synchronous wrapper
    # ------------------------------------------------------------------
    def download_sync(
        self,
        url: str,
        output_path: Path,
        options: Aria2cOptions | None = None,
    ) -> Path:
        """Synchronous version of :meth:`download`."""
        return asyncio.run(self.download(url, output_path, options))
