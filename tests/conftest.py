import pytest
from unittest.mock import MagicMock
from pathlib import Path
from core.protocols import Downloader, ProgressReporter
from core.fallback import FallbackDownloader
from core.controller import DownloadController


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
def mock_controller() -> MagicMock:
    return MagicMock(spec=DownloadController)


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    return tmp_path / "test_data"
