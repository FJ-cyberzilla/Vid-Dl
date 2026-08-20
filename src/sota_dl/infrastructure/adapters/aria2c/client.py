import asyncio
import logging
import shutil
from pathlib import Path

from sota_dl.infrastructure.adapters.aria2c.exceptions import (
    Aria2cError,
    Aria2cNotFoundError,
    Aria2cProcessError,
    Aria2cTimeoutError,
)
from sota_dl.infrastructure.adapters.aria2c.options import Aria2cOptions
from sota_dl.infrastructure.adapters.aria2c.parser import _parse_progress

logger = logging.getLogger(__name__)


class Aria2cClient:
    """
    A robust, async‑ready wrapper around the aria2c command‑line downloader.
    """

    def __init__(self, default_timeout: float | None = None) -> None:
        self.default_timeout = default_timeout

    @staticmethod
    def _validate_url(url: str) -> None:
        if not isinstance(url, str) or not url.strip():
            raise Aria2cError("URL must be a non‑empty string.")
        if not url.startswith(("http://", "https://")):
            raise Aria2cError("URL must start with http:// or https://")

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    async def _check_binary(self) -> None:
        if shutil.which("aria2c") is None:
            raise Aria2cNotFoundError(
                "aria2c not found. Install it: https://aria2.github.io"
            )

    @staticmethod
    def _build_command(
        url: str,
        output_path: Path,
        options: Aria2cOptions,
    ) -> list[str]:
        cmd = [
            "aria2c",
            "--summary-interval=0",
            "--console-log-level=notice",
            f"--max-connection-per-server={options.max_connections}",
            f"--min-split-size={options.chunk_size}",
            f"--out={output_path.name}",
            url,
        ]
        if options.headers:
            for k, v in options.headers.items():
                cmd.extend(["--header", f"{k}: {v}"])
        return cmd

    async def _read_stderr_and_track_progress(
        self,
        proc: asyncio.subprocess.Process,
        options: Aria2cOptions,
    ) -> str:
        """Reads stderr and tracks progress."""
        if not proc.stderr:
            return ""
        stderr_lines = await self._read_all_stderr(proc.stderr, options)
        return "\n".join(stderr_lines)

    async def _read_all_stderr(
        self, stderr: asyncio.StreamReader, options: Aria2cOptions
    ) -> list[str]:
        """Reads all lines from stderr."""
        lines = []
        while True:
            line = await self._read_line(stderr)
            if not line:
                break
            lines.append(line)
            await self._process_line(line, options)
        return lines

    async def _read_line(self, stderr: asyncio.StreamReader) -> str | None:
        """Reads a single line from stderr."""
        line_bytes = await stderr.readline()
        if not line_bytes:
            return None
        return line_bytes.decode("utf-8", errors="replace").rstrip()

    async def _process_line(self, line: str, options: Aria2cOptions) -> None:
        if not options.progress_callback:
            return

        pct = _parse_progress(line)
        if pct is not None:
            await asyncio.get_event_loop().run_in_executor(
                None, options.progress_callback, pct
            )

    async def _execute_attempt(
        self,
        args: list[str],
        options: Aria2cOptions,
        cwd: Path,
        timeout: float | None,
    ) -> None:
        """Executes a single download attempt."""
        proc = await self._start_process(args, cwd)
        try:
            stderr = await self._run_process_with_timeout(proc, options, timeout)
            self._check_return_code(proc, stderr)
        finally:
            await self._cleanup_process(proc)

    async def _start_process(
        self, args: list[str], cwd: Path
    ) -> asyncio.subprocess.Process:
        """Starts the aria2c process."""
        return await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )

    async def _run_process_with_timeout(
        self,
        proc: asyncio.subprocess.Process,
        options: Aria2cOptions,
        timeout: float | None,
    ) -> str:
        """Runs the process and handles timeout/reading."""
        read_task = asyncio.create_task(
            self._read_stderr_and_track_progress(proc, options)
        )
        try:
            if timeout is not None:
                await asyncio.wait_for(proc.wait(), timeout=timeout)
            else:
                await proc.wait()
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise Aria2cTimeoutError(
                f"Download timed out after {timeout} seconds."
            ) from exc
        return await read_task

    def _check_return_code(self, proc: asyncio.subprocess.Process, stderr: str) -> None:
        """Checks the process return code."""
        if proc.returncode != 0:
            raise Aria2cProcessError(
                f"aria2c exited with code {proc.returncode}", stderr
            )
        logger.debug("aria2c succeeded:\n%s", stderr)

    async def _cleanup_process(self, proc: asyncio.subprocess.Process) -> None:
        """Ensures the process is terminated."""
        if proc.returncode is None:
            proc.kill()
            await proc.wait()

    async def _run_aria2c(
        self,
        args: list[str],
        options: Aria2cOptions,
        cwd: Path,
    ) -> None:
        """Manages download retry loop."""
        timeout = (
            options.timeout if options.timeout is not None else self.default_timeout
        )

        for attempt in range(1, options.retries + 1):
            if await self._attempt_download(args, options, cwd, timeout, attempt):
                return

    async def _attempt_download(
        self,
        args: list[str],
        options: Aria2cOptions,
        cwd: Path,
        timeout: float | None,
        attempt: int,
    ) -> bool:
        """Attempts a single download and handles retry logic."""
        try:
            await self._execute_attempt(args, options, cwd, timeout)
            return True
        except (Aria2cProcessError, Aria2cTimeoutError):
            raise
        except OSError as exc:
            return await self._handle_os_error(exc, attempt, options)

    async def _handle_os_error(
        self, exc: OSError, attempt: int, options: Aria2cOptions
    ) -> bool:
        """Handles OSError retry logic."""
        logger.warning("Attempt %d failed: %s", attempt, exc)
        if attempt == options.retries:
            raise Aria2cError(
                f"Download failed after {options.retries} attempts"
            ) from exc
        await asyncio.sleep(1.5 ** (attempt - 1))
        return False

    async def download(
        self,
        url: str,
        output_path: Path,
        options: Aria2cOptions | None = None,
    ) -> Path:
        if options is None:
            options = Aria2cOptions()

        self._validate_url(url)
        self._ensure_dir(output_path)
        await self._check_binary()

        args = self._build_command(url, output_path, options)
        await self._run_aria2c(args, options, output_path.parent)
        return output_path

    def download_sync(
        self,
        url: str,
        output_path: Path,
        options: Aria2cOptions | None = None,
    ) -> Path:
        return asyncio.run(self.download(url, output_path, options))
