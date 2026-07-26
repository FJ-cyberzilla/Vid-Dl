"""State‑of‑the‑art FFmpeg media processing with async support and progress tracking."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class FFmpegError(Exception):
    """Base exception for FFmpeg processing failures."""


class FFmpegNotFoundError(FFmpegError):
    """FFmpeg binary not found or not executable."""


class FFmpegProcessError(FFmpegError):
    """FFmpeg process returned a non‑zero exit code."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class FFmpegTimeoutError(FFmpegError):
    """Operation timed out."""


# ---------------------------------------------------------------------------
# Progress parser for FFmpeg stderr
# ---------------------------------------------------------------------------
_FFMPEG_TIME_RE = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")


def _parse_time(line: str) -> float | None:
    """Extract current processing time in seconds from an ffmpeg stderr line."""
    match = _FFMPEG_TIME_RE.search(line)
    if not match:
        return None
    h, m, s = match.group(1).split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)


# ---------------------------------------------------------------------------
# FFmpegProcessor
# ---------------------------------------------------------------------------
class FFmpegProcessor:
    """
    A modern, async‑first FFmpeg wrapper.

    Parameters:
        ffmpeg_path: Path or name of the ffmpeg binary. Defaults to ``"ffmpeg"``.
        ffprobe_path: Path or name of the ffprobe binary. Defaults to ``"ffprobe"``.
        default_timeout: Default timeout (seconds) for operations. ``None`` = no limit.

    Usage:
        proc = FFmpegProcessor()
        await proc.merge_audio_video(
            Path("video.mp4"), Path("audio.aac"), Path("out.mp4"),
            progress_callback=lambda t: print(f"Processed {t:.1f}s")
        )
    """

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
        default_timeout: float | None = None,
    ) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.default_timeout = default_timeout

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _check_file(path: Path) -> None:
        """Raise if *path* does not exist or is not a file."""
        if not path.is_file():
            raise FFmpegError(f"Input file does not exist: {path}")

    async def check_ffmpeg(self) -> None:
        """Verify that ffmpeg is callable (public for pre‑flight checks)."""
        try:
            subprocess_proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path,
                "-version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await subprocess_proc.wait()
            if subprocess_proc.returncode != 0:
                raise FFmpegNotFoundError(
                    f"FFmpeg exited with code {subprocess_proc.returncode}"
                )
        except FileNotFoundError as err:
            raise FFmpegNotFoundError(
                f"FFmpeg binary not found: {self.ffmpeg_path}"
            ) from err

    # ------------------------------------------------------------------
    # Core async runner with progress
    # ------------------------------------------------------------------
    async def _run_ffmpeg(
        self,
        args: list[str],
        progress_callback: Callable[[float], Any] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Run an ffmpeg command asynchronously.

        Args:
            args: Command arguments (including the binary name as first element).
            progress_callback: Called with the current time in seconds from ffmpeg.
            timeout: If given, raises :class:`FFmpegTimeoutError`
                after this many seconds.
            **kwargs: Extra keyword arguments for :func:`asyncio.wait_for`.

        Raises:
            FFmpegProcessError: On non‑zero exit.
            FFmpegTimeoutError: On timeout.
        """
        if timeout is None:
            timeout = self.default_timeout

        subproc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Read stderr line by line while the process runs
            async def read_stderr() -> str:
                stderr_lines = []
                if subproc.stderr:
                    while True:
                        line_bytes = await subproc.stderr.readline()
                        if not line_bytes:
                            break
                        line = line_bytes.decode("utf-8", errors="replace").rstrip()
                        stderr_lines.append(line)
                        if progress_callback:
                            t = _parse_time(line)
                            if t is not None:
                                # Fire callback for each valid time update
                                await asyncio.get_event_loop().run_in_executor(
                                    None, progress_callback, t
                                )
                return "\n".join(stderr_lines)

            # Wait for both stderr reading and process completion with timeout
            read_task = asyncio.create_task(read_stderr())
            try:
                await asyncio.wait_for(subproc.wait(), timeout=timeout, **kwargs)
            except asyncio.TimeoutError as err:
                subproc.kill()
                await subproc.wait()  # clean up
                raise FFmpegTimeoutError(
                    f"Operation timed out after {timeout} seconds."
                ) from err

            stderr = await read_task

            if subproc.returncode != 0:
                raise FFmpegProcessError(
                    f"FFmpeg exited with code {subproc.returncode}",
                    stderr=stderr,
                )
            logger.debug("FFmpeg finished successfully.\n%s", stderr)
        finally:
            if subproc.returncode is None:
                subproc.kill()
                await subproc.wait()

    # ------------------------------------------------------------------
    # Public async methods
    # ------------------------------------------------------------------
    async def merge_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        *,
        progress_callback: Callable[[float], Any] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """
        Merge a video and an audio stream, copying both codecs.

        Parameters:
            video_path: Path to the video file.
            audio_path: Path to the audio file.
            output_path: Destination path for the merged file.
            progress_callback: Called periodically with the current time (seconds).
            timeout: Override the default timeout.

        Returns:
            The output path.
        """
        self._check_file(video_path)
        self._check_file(audio_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            self.ffmpeg_path,
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c",
            "copy",
            "-y",
            "-progress",
            "pipe:2",  # ensure time= lines appear on stderr
            str(output_path),
        ]

        await self._run_ffmpeg(
            args, progress_callback=progress_callback, timeout=timeout
        )
        return output_path

    async def extract_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: str = "00:00:05",
        *,
        timeout: float | None = None,
    ) -> Path:
        """
        Extract a single frame as a thumbnail.

        Parameters:
            video_path: Path to the video file.
            output_path: Where to save the thumbnail image.
            timestamp: Time position in HH:MM:SS or seconds format.
            timeout: Override the default timeout.

        Returns:
            The output path.
        """
        self._check_file(video_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            self.ffmpeg_path,
            "-i",
            str(video_path),
            "-ss",
            timestamp,
            "-vframes",
            "1",
            "-y",
            str(output_path),
        ]
        await self._run_ffmpeg(args, timeout=timeout)
        return output_path

    # ------------------------------------------------------------------
    # Synchronous wrappers (for non‑async code)
    # ------------------------------------------------------------------
    def merge_audio_video_sync(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        *,
        progress_callback: Callable[[float], Any] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """Synchronous version of :meth:`merge_audio_video`."""
        return asyncio.run(
            self.merge_audio_video(
                video_path,
                audio_path,
                output_path,
                progress_callback=progress_callback,
                timeout=timeout,
            )
        )

    def extract_thumbnail_sync(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: str = "00:00:05",
        *,
        timeout: float | None = None,
    ) -> Path:
        """Synchronous version of :meth:`extract_thumbnail`."""
        return asyncio.run(
            self.extract_thumbnail(
                video_path,
                output_path,
                timestamp,
                timeout=timeout,
            )
        )


# ---------------------------------------------------------------------------
# Quick self‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    proc = FFmpegProcessor()

    async def _check_via_test() -> None:
        """Run a quick verification that FFmpeg is reachable."""
        await proc.check_ffmpeg()
        print("FFmpegProcessor is ready.")

    asyncio.run(_check_via_test())
