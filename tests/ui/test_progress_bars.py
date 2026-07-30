import pytest
from unittest.mock import MagicMock, patch
from sota_dl.ui.progress_bars import (
    RichProgressReporter,
    get_sota_progress,
    reset_progress,
)
from rich.progress import Progress


@pytest.fixture(autouse=True)
def cleanup_progress():
    reset_progress()
    yield
    reset_progress()


def test_rich_progress_reporter():
    mock_progress = MagicMock(spec=Progress)
    reporter = RichProgressReporter(mock_progress)

    task_id = reporter.add_task("test", total=100)
    assert task_id == 0  # RichTaskID(0)
    mock_progress.add_task.assert_called_once_with("test", total=100)

    reporter.update(task_id, completed=50)
    mock_progress.update.assert_called_with(0, completed=50)

    reporter.advance(task_id, amount=10)
    mock_progress.advance.assert_called_with(0, advance=10)

    reporter.reset(task_id, total=200)
    mock_progress.reset.assert_called_with(0, total=200)

    reporter.remove_task(task_id)
    mock_progress.remove_task.assert_called_with(0)


def test_get_sota_progress_tty():
    with patch("sys.stdout.isatty", return_value=True):
        reporter = get_sota_progress()
        assert isinstance(reporter, RichProgressReporter)
        # Should be a singleton
        assert get_sota_progress() is reporter


def test_get_sota_progress_not_tty():
    with patch("sys.stdout.isatty", return_value=False):
        # We need a fresh call to test the non-tty path
        reset_progress()
        reporter = get_sota_progress()
        assert isinstance(reporter, RichProgressReporter)
        assert reporter._progress.disable is True
