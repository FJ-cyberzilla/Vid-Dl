import pytest
from typing import Any
from unittest.mock import MagicMock, patch
from pathlib import Path
from sota_dl.ui.download_controller import handle_results, execute_download
from sota_dl.core.models import DownloadResult, DownloadStatus


@pytest.fixture
def mock_result() -> DownloadResult:
    return DownloadResult(
        status=DownloadStatus.COMPLETED,
        file_path=Path("video.mp4"),
    )


def test_handle_results_success(capsys: Any, tmp_path: Path) -> None:
    results = [
        DownloadResult(status=DownloadStatus.COMPLETED, file_path=Path("p1")),
        DownloadResult(status=DownloadStatus.COMPLETED, file_path=Path("p2")),
    ]
    output_path = tmp_path

    with patch("sota_dl.ui.download_controller.print_success") as mock_print:
        handle_results(results, output_path)
        mock_print.assert_called_once()
        assert "2 downloads completed" in mock_print.call_args[0][0]


def test_handle_results_mixed(capsys: Any, tmp_path: Path) -> None:
    results = [
        DownloadResult(status=DownloadStatus.COMPLETED, file_path=Path("p1")),
        DownloadResult(status=DownloadStatus.FAILED, file_path=Path("p2")),
    ]
    output_path = tmp_path

    with patch("sota_dl.ui.download_controller.console.print") as mock_print:
        handle_results(results, output_path)
        # Check if yellow text is printed for mixed results
        assert any(
            "1 succeeded, 1 failed" in str(call) for call in mock_print.call_args_list
        )


@patch("sota_dl.ui.download_controller.get_quality_choice")
@patch("sota_dl.ui.download_controller._get_downloader_factory")
@patch("sota_dl.ui.download_controller.handle_results")
@patch("sota_dl.ui.download_controller.input")
@patch("sota_dl.ui.download_controller.console.print")
def test_execute_download_success(
    mock_print: Any,
    mock_input: Any,
    mock_handle: Any,
    mock_factory: Any,
    mock_quality: Any,
    tmp_path: Path,
) -> None:
    mock_quality.return_value = "best"
    mock_service_instance = MagicMock()
    mock_factory.return_value.return_value = mock_service_instance

    execute_download("1", "target_url", tmp_path)

    mock_service_instance.process_target.assert_called_once()
    mock_handle.assert_called_once()


@patch("sota_dl.ui.download_controller.get_quality_choice")
@patch("sota_dl.ui.download_controller._get_downloader_factory")
@patch("sota_dl.ui.download_controller.input")
@patch("sota_dl.ui.download_controller.console.print")
def test_execute_download_interrupt(
    mock_print: Any,
    mock_input: Any,
    mock_factory: Any,
    mock_quality: Any,
    tmp_path: Path,
) -> None:
    mock_quality.return_value = "best"
    mock_service_instance = MagicMock()
    mock_service_instance.process_target.side_effect = KeyboardInterrupt
    mock_factory.return_value.return_value = mock_service_instance

    execute_download("1", "target_url", tmp_path)

    mock_service_instance.cancel.assert_called_once()
