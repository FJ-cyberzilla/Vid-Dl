import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from sota_dl.core.config_service import ConfigurationService


@pytest.fixture
def mock_settings() -> MagicMock:
    return MagicMock()


@pytest.fixture
def config_service(mock_settings: MagicMock) -> ConfigurationService:
    return ConfigurationService(mock_settings)


def test_update_cookies_path_invalid(config_service: ConfigurationService) -> None:
    success, message = config_service.update_cookies_path("")
    assert not success
    assert message == "No path provided"


def test_update_cookies_path_not_exists(config_service: ConfigurationService) -> None:
    success, message = config_service.update_cookies_path("/non/existent/path")
    assert not success
    assert "Source not found" in message


def test_update_cookies_path_success(
    config_service: ConfigurationService, mock_settings: MagicMock, tmp_path: Path
) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.touch()

    success, message = config_service.update_cookies_path(str(cookie_file))
    assert success
    assert "Source updated" in message
    assert cookie_file.expanduser().absolute() == mock_settings.COOKIES_PATH


def test_update_download_path_invalid(config_service: ConfigurationService) -> None:
    success, message = config_service.update_download_path("")
    assert not success
    assert message == "No path provided"


def test_update_download_path_success(
    config_service: ConfigurationService, mock_settings: MagicMock, tmp_path: Path
) -> None:
    # We need to mock _is_writable which is imported in config_service
    # from utils or infrastructure, or it is part of settings?
    # In config_service, update_download_path checks path.exists() and
    # if it's writable.
    success, message = config_service.update_download_path(str(tmp_path))
    assert success
    assert "Target updated" in message
    assert tmp_path.expanduser().absolute() == mock_settings.ENV_OVERRIDE


def test_extract_browser_cookies_fail(config_service: ConfigurationService) -> None:
    with patch(
        "sota_dl.infrastructure.adapters.browser_cookies.BrowserCookieAdapter.get_cookies_for_url",
        side_effect=Exception("Extraction error"),
    ):
        success, message = config_service.extract_browser_cookies()
        assert not success
        assert "Failed to extract browser cookies" in message


def test_extract_browser_cookies_success(config_service: ConfigurationService) -> None:
    with patch(
        "sota_dl.infrastructure.adapters.browser_cookies.BrowserCookieAdapter.get_cookies_for_url",
        return_value={"test": "cookie"},
    ):
        success, message = config_service.extract_browser_cookies()
        assert success
        assert "Browser cookies extracted successfully" in message
