from pathlib import Path
import pytest
from sota_dl.infrastructure.file_system import (
    FileSystemManager,
    InsufficientSpaceError,
)


@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    return tmp_path / "video_downloader"


@pytest.fixture
def fs_manager(temp_root: Path) -> FileSystemManager:
    return FileSystemManager(temp_dir=temp_root)


def test_create_temp_file(fs_manager: FileSystemManager) -> None:
    tmp_file = fs_manager.create_temp_file(suffix=".test")
    assert tmp_file.exists()
    assert tmp_file.suffix == ".test"
    fs_manager.cleanup(tmp_file)
    assert not tmp_file.exists()


def test_create_temp_dir(fs_manager: FileSystemManager) -> None:
    tmp_dir = fs_manager.create_temp_dir(prefix="test_")
    assert tmp_dir.exists()
    assert tmp_dir.is_dir()
    fs_manager.cleanup(tmp_dir)
    assert not tmp_dir.exists()


def test_get_disk_usage(fs_manager: FileSystemManager) -> None:
    usage = fs_manager.get_disk_usage()
    assert "total" in usage
    assert "used" in usage
    assert "free" in usage
    assert usage["free"] >= 0


def test_ensure_free_space(fs_manager: FileSystemManager) -> None:
    # Check with 0 required MB (should always be true)
    assert fs_manager.ensure_free_space(0) is True
    # Check with a huge amount that should be false
    assert fs_manager.ensure_free_space(999999999) is False


def test_require_free_space_raises(fs_manager: FileSystemManager) -> None:
    with pytest.raises(InsufficientSpaceError):
        fs_manager.require_free_space(999999999)


def test_copy_move(fs_manager: FileSystemManager, tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("hello")
    dest_copy = tmp_path / "copy.txt"
    dest_move = tmp_path / "move.txt"

    fs_manager.copy_file(src, dest_copy)
    assert dest_copy.exists()
    assert dest_copy.read_text() == "hello"

    fs_manager.move_file(dest_copy, dest_move)
    assert dest_move.exists()
    assert not dest_copy.exists()

    fs_manager.cleanup(src)
    fs_manager.cleanup(dest_move)
