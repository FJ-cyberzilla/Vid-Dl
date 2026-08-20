from typing import Any
from unittest.mock import patch
from sota_dl.ui.settings_controller import update_cookies, update_download_path


@patch("sota_dl.ui.settings_controller.Prompt.ask")
@patch("sota_dl.ui.settings_controller.print_success")
@patch("sota_dl.ui.settings_controller.print_error")
@patch("sota_dl.ui.settings_controller._config_service")
def test_update_cookies_success(
    mock_service: Any, mock_error: Any, mock_success: Any, mock_prompt: Any
) -> None:
    mock_prompt.return_value = "cookies.txt"
    mock_service.update_cookies_path.return_value = (
        True,
        "Source updated: cookies.txt",
    )

    update_cookies()

    mock_service.update_cookies_path.assert_called_once_with("cookies.txt")
    mock_success.assert_called_once_with("Source updated: cookies.txt")
    mock_error.assert_not_called()


@patch("sota_dl.ui.settings_controller.Prompt.ask")
@patch("sota_dl.ui.settings_controller.print_success")
@patch("sota_dl.ui.settings_controller.print_error")
@patch("sota_dl.ui.settings_controller._config_service")
def test_update_cookies_failure(
    mock_service: Any, mock_error: Any, mock_success: Any, mock_prompt: Any
) -> None:
    mock_prompt.return_value = "non_existent.txt"
    mock_service.update_cookies_path.return_value = (False, "Source not found")

    update_cookies()

    mock_service.update_cookies_path.assert_called_once_with("non_existent.txt")
    mock_error.assert_called_once_with("Source not found")
    mock_success.assert_not_called()


@patch("sota_dl.ui.settings_controller.Prompt.ask")
@patch("sota_dl.ui.settings_controller.print_success")
@patch("sota_dl.ui.settings_controller.print_error")
@patch("sota_dl.ui.settings_controller._config_service")
def test_update_download_path_success(
    mock_service: Any, mock_error: Any, mock_success: Any, mock_prompt: Any
) -> None:
    mock_prompt.return_value = "downloads"
    mock_service.update_download_path.return_value = (True, "Target updated: downloads")

    update_download_path()

    mock_service.update_download_path.assert_called_once_with("downloads")
    mock_success.assert_called_once_with("Target updated: downloads")
    mock_error.assert_not_called()


@patch("sota_dl.ui.settings_controller.Prompt.ask")
@patch("sota_dl.ui.settings_controller.print_success")
@patch("sota_dl.ui.settings_controller.print_error")
@patch("sota_dl.ui.settings_controller._config_service")
def test_update_download_path_failure(
    mock_service: Any, mock_error: Any, mock_success: Any, mock_prompt: Any
) -> None:
    mock_prompt.return_value = "readonly"
    mock_service.update_download_path.return_value = (False, "Target not writable")

    update_download_path()

    mock_service.update_download_path.assert_called_once_with("readonly")
    mock_error.assert_called_once_with("Target not writable")
    mock_success.assert_not_called()
