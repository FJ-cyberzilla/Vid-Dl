import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from infrastructure.aria2c import (
    Aria2cClient,
    Aria2cOptions,
    Aria2cError,
    Aria2cNotFoundError,
    Aria2cTimeoutError,
    _parse_progress,
)


def test_parse_progress() -> None:
    assert _parse_progress("some output (25%) more") == 25.0
    assert _parse_progress("no progress") is None


@pytest.fixture
def aria2c_client() -> Aria2cClient:
    return Aria2cClient()


def test_validate_url(aria2c_client: Aria2cClient) -> None:
    aria2c_client._validate_url("https://example.com")
    with pytest.raises(Aria2cError, match="URL must be a non‑empty string"):
        aria2c_client._validate_url("")
    with pytest.raises(Aria2cError, match="URL must start with http"):
        aria2c_client._validate_url("ftp://example.com")


@pytest.mark.asyncio
async def test_check_binary_not_found(aria2c_client: Aria2cClient) -> None:
    with patch("shutil.which", return_value=None), pytest.raises(Aria2cNotFoundError):
        await aria2c_client._check_binary()


def test_build_command(aria2c_client: Aria2cClient) -> None:
    options = Aria2cOptions(headers={"Auth": "Token"})
    # Using a path that is not in /tmp
    cmd = aria2c_client._build_command("https://url", Path("out.mp4"), options)
    assert "aria2c" in cmd
    assert "--header" in cmd
    assert "Auth: Token" in cmd


@pytest.mark.asyncio
async def test_run_aria2c_success(aria2c_client: Aria2cClient, tmp_path: Path) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = AsyncMock()
        mock_subproc.wait.return_value = 0
        mock_subproc.returncode = 0
        mock_subproc.stderr.readline.side_effect = [b"(50%)\n", b""]
        mock_exec.return_value = mock_subproc

        progress = []
        options = Aria2cOptions(
            progress_callback=lambda p: progress.append(p), retries=1
        )
        await aria2c_client._run_aria2c(["aria2c"], options, tmp_path)
        assert progress == [50.0]


@pytest.mark.asyncio
async def test_run_aria2c_timeout(aria2c_client: Aria2cClient, tmp_path: Path) -> None:
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_subproc = MagicMock()
        mock_subproc.kill = MagicMock()

        # Use a Future instead of a coroutine to avoid "never awaited" warnings
        # when asyncio.wait_for is patched to raise TimeoutError.
        f: asyncio.Future[int] = asyncio.Future()
        f.set_result(0)
        mock_subproc.wait = MagicMock(return_value=f)
        mock_subproc.returncode = None
        mock_exec.return_value = mock_subproc

        with (
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError),
            pytest.raises(Aria2cTimeoutError),
        ):
            await aria2c_client._run_aria2c(
                ["aria2c"], Aria2cOptions(timeout=0.1), tmp_path
            )
        assert mock_subproc.kill.called


@pytest.mark.asyncio
async def test_download_full_cycle(aria2c_client: Aria2cClient, tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    with (
        patch.object(aria2c_client, "_check_binary", new_callable=AsyncMock),
        patch.object(aria2c_client, "_run_aria2c", new_callable=AsyncMock) as mock_run,
    ):
        result = await aria2c_client.download("https://test.com/file", out)
        assert result == out
        mock_run.assert_called_once()
