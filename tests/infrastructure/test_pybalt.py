import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from sota_dl.infrastructure.extensions.pybalt import (
    PyBaltEngine,
    ExtractOptions,
    MissingDependencyError,
    StatusParent,
)


@pytest.fixture
def engine() -> PyBaltEngine:
    # Inject a mock client
    mock_client = MagicMock()
    # Ensure download method is an AsyncMock
    mock_client.download = AsyncMock()
    return PyBaltEngine(pybalt_client=mock_client)


def test_extract_missing_dependency(tmp_path: Path) -> None:
    # Test without injection
    engine = PyBaltEngine(pybalt_client=None)
    # Force client to be None even if pybalt is installed
    engine._client = None
    with pytest.raises(MissingDependencyError):
        engine.extract("https://example.com", tmp_path / "out.mp4")


@pytest.mark.asyncio
async def test_extract_async_success(tmp_path: Path) -> None:
    # Setup mock client
    mock_client = AsyncMock()
    # Simulate pybalt returning a file path
    downloaded_file = tmp_path / "downloaded.mp4"
    downloaded_file.touch()
    mock_client.download.return_value = str(downloaded_file)

    engine = PyBaltEngine(pybalt_client=mock_client)

    output_path = tmp_path / "final.mp4"

    path = await engine.extract_async("https://example.com", output_path)

    assert path == output_path
    assert output_path.exists()
    mock_client.download.assert_called_once()


@pytest.mark.asyncio
async def test_extract_async_with_status_parent(tmp_path: Path) -> None:
    # Setup mock client
    mock_client = AsyncMock()
    downloaded_file = tmp_path / "downloaded.mp4"
    downloaded_file.touch()
    mock_client.download.return_value = str(downloaded_file)

    engine = PyBaltEngine(pybalt_client=mock_client)

    status_parent = StatusParent()
    options = ExtractOptions(status_parent=status_parent)

    output_path = tmp_path / "final.mp4"

    await engine.extract_async("https://example.com", output_path, options=options)

    # Verify status_parent was passed
    mock_client.download.assert_called_once_with(
        "https://example.com",
        videoQuality="best",
        remux=True,
        status_parent=status_parent,
    )


@pytest.mark.asyncio
async def test_extract_async_retries(tmp_path: Path) -> None:
    mock_client = AsyncMock()

    downloaded_file = tmp_path / "downloaded.mp4"
    downloaded_file.touch()

    engine = PyBaltEngine(pybalt_client=mock_client)

    output_path = tmp_path / "final.mp4"

    # We expect this to raise ExtractionError because _perform_extraction_async
    # wraps all exceptions
    mock_client.download.side_effect = [
        Exception("Fail"),
        Exception("Fail"),
        str(downloaded_file),
    ]

    path = await engine.extract_async(
        "https://example.com", output_path, options=ExtractOptions(retries=3)
    )

    assert path == output_path
    assert mock_client.download.call_count == 3
