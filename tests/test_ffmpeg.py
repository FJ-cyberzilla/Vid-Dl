import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.ffmpeg import (
    FFmpegProcessor,
    FFmpegError,
    FFmpegNotFoundError,
    FFmpegProcessError,
    FFmpegTimeoutError,
    _parse_time,
)


def test_parse_time() -> None:
    assert (
        _parse_time(
            "frame=  100 fps= 25 q=-1.0 Lsize=    1000kB time=00:00:04.00 "
            "bitrate=2000.0kbits/s speed=1.0x"
        )
        == 4.0
    )
    assert _parse_time("time=01:02:03.45") == 3600 + 120 + 3.45
    assert _parse_time("no time here") is None


@pytest.fixture
def ffmpeg_proc() -> FFmpegProcessor:
    return FFmpegProcessor()


def test_check_file_exists(tmp_path: Path) -> None:
    f = tmp_path / "exists.mp4"
    f.touch()
    FFmpegProcessor._check_file(f)


def test_check_file_missing() -> None:
    with pytest.raises(FFmpegError, match="Input file does not exist"):
        FFmpegProcessor._check_file(Path("missing.mp4"))


@pytest.mark.asyncio
async def test_check_ffmpeg_success(ffmpeg_proc: FFmpegProcessor) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = AsyncMock()
        mock_subproc.wait.return_value = 0
        mock_subproc.returncode = 0
        mock_exec.return_value = mock_subproc

        await ffmpeg_proc.check_ffmpeg()
        mock_exec.assert_called_once_with(
            "ffmpeg",
            "-version",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )


@pytest.mark.asyncio
async def test_check_ffmpeg_not_found(ffmpeg_proc: FFmpegProcessor) -> None:
    with (
        patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError),
        pytest.raises(FFmpegNotFoundError, match="FFmpeg binary not found"),
    ):
        await ffmpeg_proc.check_ffmpeg()


@pytest.mark.asyncio
async def test_check_ffmpeg_error_code(ffmpeg_proc: FFmpegProcessor) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = AsyncMock()
        mock_subproc.wait.return_value = 1
        mock_subproc.returncode = 1
        mock_exec.return_value = mock_subproc

        with pytest.raises(FFmpegNotFoundError, match="FFmpeg exited with code 1"):
            await ffmpeg_proc.check_ffmpeg()


@pytest.mark.asyncio
async def test_run_ffmpeg_success(ffmpeg_proc: FFmpegProcessor) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = AsyncMock()
        mock_subproc.wait.return_value = 0
        mock_subproc.returncode = 0
        mock_subproc.stderr.readline.side_effect = [
            b"time=00:00:01.00\n",
            b"time=00:00:02.00\n",
            b"",
        ]
        mock_exec.return_value = mock_subproc

        progress_updates = []

        def callback(t: float) -> None:
            progress_updates.append(t)

        await ffmpeg_proc._run_ffmpeg(
            ["ffmpeg", "-i", "in.mp4", "out.mp4"],
            progress_callback=callback,
        )

        assert progress_updates == [1.0, 2.0]
        assert mock_subproc.wait.called


@pytest.mark.asyncio
async def test_run_ffmpeg_process_error(ffmpeg_proc: FFmpegProcessor) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = AsyncMock()
        mock_subproc.wait.return_value = 1
        mock_subproc.returncode = 1
        mock_subproc.stderr.readline.side_effect = [b"Error message\n", b""]
        mock_exec.return_value = mock_subproc

        with pytest.raises(FFmpegProcessError) as exc:
            await ffmpeg_proc._run_ffmpeg(["ffmpeg"])
        assert "exited with code 1" in str(exc.value)
        assert exc.value.stderr == "Error message"


@pytest.mark.asyncio
async def test_run_ffmpeg_timeout(ffmpeg_proc: FFmpegProcessor) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = MagicMock()
        mock_subproc.kill = MagicMock()

        # Use Future instead of AsyncMock to avoid unawaited coroutine warnings
        # when asyncio.wait_for is patched to raise TimeoutError.
        f: asyncio.Future[int] = asyncio.Future()
        f.set_result(0)
        mock_subproc.wait = MagicMock(return_value=f)
        mock_exec.return_value = mock_subproc

        # Mock wait to raise TimeoutError
        with (
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError),
            pytest.raises(FFmpegTimeoutError, match="timed out after 1.0 seconds"),
        ):
            await ffmpeg_proc._run_ffmpeg(["ffmpeg"], timeout=1.0)
        assert mock_subproc.kill.called


@pytest.mark.asyncio
async def test_merge_audio_video(ffmpeg_proc: FFmpegProcessor, tmp_path: Path) -> None:
    v = tmp_path / "v.mp4"
    a = tmp_path / "a.mp4"
    out = tmp_path / "out.mp4"
    v.touch()
    a.touch()

    with patch.object(ffmpeg_proc, "_run_ffmpeg", new_callable=AsyncMock) as mock_run:
        await ffmpeg_proc.merge_audio_video(v, a, out)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-c" in args
        assert "copy" in args
        assert str(v) in args
        assert str(a) in args
        assert str(out) in args


@pytest.mark.asyncio
async def test_extract_thumbnail(ffmpeg_proc: FFmpegProcessor, tmp_path: Path) -> None:
    v = tmp_path / "v.mp4"
    out = tmp_path / "thumb.jpg"
    v.touch()

    with patch.object(ffmpeg_proc, "_run_ffmpeg", new_callable=AsyncMock) as mock_run:
        await ffmpeg_proc.extract_thumbnail(v, out, timestamp="00:01:00")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-ss" in args
        assert "00:01:00" in args
        assert "-vframes" in args
        assert "1" in args


def test_sync_wrappers(ffmpeg_proc: FFmpegProcessor, tmp_path: Path) -> None:
    v = tmp_path / "v.mp4"
    a = tmp_path / "a.mp4"
    out = tmp_path / "out.mp4"
    v.touch()
    a.touch()

    with patch.object(
        ffmpeg_proc, "merge_audio_video", new_callable=AsyncMock
    ) as mock_async:
        ffmpeg_proc.merge_audio_video_sync(v, a, out)
        mock_async.assert_called_once()

    with patch.object(
        ffmpeg_proc, "extract_thumbnail", new_callable=AsyncMock
    ) as mock_async:
        ffmpeg_proc.extract_thumbnail_sync(v, out)
        mock_async.assert_called_once()
