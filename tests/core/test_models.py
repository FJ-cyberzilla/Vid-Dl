from pathlib import Path
from sota_dl.core.models import (
    DownloadOptions,
    DownloadResult,
    VideoMetadata,
    DownloadTask,
    DownloadStatus,
)


def test_download_options_defaults() -> None:
    options = DownloadOptions()
    assert options.quality == "best"
    assert options.retries == 3
    assert options.output_dir == Path(".")


def test_download_result_success(tmp_path: Path) -> None:
    temp_path = tmp_path / "file.mp4"
    result = DownloadResult(status=DownloadStatus.COMPLETED, file_path=temp_path)
    assert result.status == DownloadStatus.COMPLETED
    assert result.file_path == temp_path


def test_video_metadata_validation() -> None:
    metadata = VideoMetadata(title="Test", url="http://test.com", duration=10)
    assert metadata.title == "Test"
    assert metadata.url == "http://test.com"
    assert metadata.get_info() == "Test (10s)"

    metadata_no_duration = VideoMetadata(title="Test", url="http://test.com")
    assert metadata_no_duration.get_info() == "Test (unknowns)"


def test_download_task_creation(tmp_path: Path) -> None:
    metadata = VideoMetadata(title="Test", url="http://test.com")
    task = DownloadTask(task_id="1", metadata=metadata, save_path=str(tmp_path))
    assert task.task_id == "1"
    assert task.status == DownloadStatus.PENDING
