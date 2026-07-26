import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from infrastructure.pybalt import (
    PyBaltEngine,
    ExtractOptions,
    MissingDependencyError,
    ExtractionError,
)


@pytest.fixture
def engine() -> PyBaltEngine:
    return PyBaltEngine()


def test_extract_missing_dependency(engine: PyBaltEngine, tmp_path: Path) -> None:
    with pytest.raises(MissingDependencyError):
        engine.extract("https://example.com", tmp_path / "out.mp4")


@patch.object(PyBaltEngine, "_extract_impl")
def test_extract_retries(
    mock_impl: MagicMock, engine: PyBaltEngine, tmp_path: Path
) -> None:
    # Make _extract_impl raise an ExtractionError twice, then succeed
    mock_impl.side_effect = [
        ExtractionError("Fail"),
        ExtractionError("Fail"),
        tmp_path / "out.mp4",
    ]

    options = ExtractOptions(retries=3)
    path = engine.extract("https://example.com", tmp_path / "out.mp4", options=options)

    assert path == tmp_path / "out.mp4"
    assert mock_impl.call_count == 3


@pytest.mark.asyncio
async def test_extract_async(engine: PyBaltEngine, tmp_path: Path) -> None:
    # Patch extract method
    with patch.object(
        engine, "extract", return_value=tmp_path / "out.mp4"
    ) as mock_extract:
        path = await engine.extract_async("https://example.com", tmp_path / "out.mp4")
        assert path == tmp_path / "out.mp4"
        mock_extract.assert_called_once()
