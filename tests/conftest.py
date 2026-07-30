import pytest
from unittest.mock import MagicMock
from pathlib import Path
from sota_dl.core.protocols import Downloader, ProgressReporter
from sota_dl.core.fallback import FallbackDownloader


@pytest.fixture
def mock_downloader() -> MagicMock:
    return MagicMock(spec=Downloader)


@pytest.fixture
def mock_fallback_downloader() -> MagicMock:
    return MagicMock(spec=FallbackDownloader)


@pytest.fixture
def mock_progress_reporter() -> MagicMock:
    return MagicMock(spec=ProgressReporter)


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    return tmp_path / "test_data"
