import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from sota_dl.ui.download_handler import handle_results, execute_download
from sota_dl.core.models import DownloadResult, DownloadStatus


@pytest.fixture
def mock_result():
    return DownloadResult(
        title="Test Video",
        url="http://test.url",
        status=DownloadStatus.COMPLETED,
        path=Path("video.mp4"),
    )


def test_handle_results_success(capsys, tmp_path):
    results = [
        DownloadResult(
            title="1", url="u1", status=DownloadStatus.COMPLETED, path=Path("p1")
        ),
        DownloadResult(
            title="2", url="u2", status=DownloadStatus.COMPLETED, path=Path("p2")
        ),
    ]
    output_path = tmp_path

    with patch("sota_dl.ui.download_handler.print_success") as mock_print:
        handle_results(results, output_path)
        mock_print.assert_called_once()
        assert "2 downloads completed" in mock_print.call_args[0][0]


def test_handle_results_mixed(capsys, tmp_path):
    results = [
        DownloadResult(
            title="1", url="u1", status=DownloadStatus.COMPLETED, path=Path("p1")
        ),
        DownloadResult(
            title="2", url="u2", status=DownloadStatus.FAILED, path=Path("p2")
        ),
    ]
    output_path = tmp_path

    with patch("sota_dl.ui.download_handler.console.print") as mock_print:
        handle_results(results, output_path)
        # Check if yellow text is printed for mixed results
        assert any(
            "1 succeeded, 1 failed" in str(call) for call in mock_print.call_args_list
        )


@patch("sota_dl.ui.download_handler.get_quality_choice")
@patch("sota_dl.ui.download_handler._get_downloader_factory")
@patch("sota_dl.ui.download_handler.DownloadService")
@patch("sota_dl.ui.download_handler.handle_results")
@patch("sota_dl.ui.download_handler.input")
@patch("sota_dl.ui.download_handler.console.print")
def test_execute_download_success(
    mock_print,
    mock_input,
    mock_handle,
    mock_service,
    mock_factory,
    mock_quality,
    tmp_path,
):
    mock_quality.return_value = "best"
    mock_service_instance = MagicMock()
    mock_service.return_value = mock_service_instance

    execute_download("1", "target_url", tmp_path)

    mock_service_instance.process_target.assert_called_once()
    mock_handle.assert_called_once()


@patch("sota_dl.ui.download_handler.get_quality_choice")
@patch("sota_dl.ui.download_handler._get_downloader_factory")
@patch("sota_dl.ui.download_handler.DownloadService")
@patch("sota_dl.ui.download_handler.input")
@patch("sota_dl.ui.download_handler.console.print")
def test_execute_download_interrupt(
    mock_print, mock_input, mock_service, mock_factory, mock_quality, tmp_path
):
    mock_quality.return_value = "best"
    mock_service_instance = MagicMock()
    mock_service_instance.process_target.side_effect = KeyboardInterrupt
    mock_service.return_value = mock_service_instance

    execute_download("1", "target_url", tmp_path)

    mock_service_instance.cancel.assert_called_once()
