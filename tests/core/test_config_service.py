import pytest
from unittest.mock import patch
from sota_dl.core.config_service import ConfigurationService


@pytest.fixture
def config_service():
    return ConfigurationService()


def test_update_cookies_path_invalid(config_service):
    success, message = config_service.update_cookies_path("")
    assert not success
    assert message == "No path provided"


def test_update_cookies_path_not_exists(config_service):
    success, message = config_service.update_cookies_path("/non/existent/path")
    assert not success
    assert "Source not found" in message


def test_update_cookies_path_success(config_service, tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.touch()

    with patch("sota_dl.config.settings.COOKIES_PATH", new=None), \
            patch("sota_dl.core.config_service.settings") as mock_settings:
        # Patch settings directly to mock the settings object in the module.
        success, message = config_service.update_cookies_path(str(cookie_file))
        assert success
        assert "Source updated" in message
        assert cookie_file.expanduser().absolute() == mock_settings.COOKIES_PATH


def test_update_download_path_invalid(config_service):
    success, message = config_service.update_download_path("")
    assert not success
    assert message == "No path provided"


def test_update_download_path_success(config_service, tmp_path):
    # Mock settings._is_writable
    with patch("sota_dl.core.config_service.settings") as mock_settings:
        mock_settings._is_writable.return_value = True

        success, message = config_service.update_download_path(str(tmp_path))
        assert success
        assert "Target updated" in message
        assert tmp_path.expanduser().absolute() == mock_settings.ENV_OVERRIDE


def test_extract_browser_cookies_fail(config_service):
    with patch(
        "sota_dl.infrastructure.adapters.browser_cookies.BrowserCookieAdapter.get_cookies_for_url",
        return_value=None,
    ):
        success, message = config_service.extract_browser_cookies()
        assert not success
        assert "Failed to extract cookies" in message


def test_extract_browser_cookies_success(config_service):
    with patch(
        "sota_dl.infrastructure.adapters.browser_cookies.BrowserCookieAdapter.get_cookies_for_url",
        return_value={"test": "cookie"},
    ):
        success, message = config_service.extract_browser_cookies()
        assert success
        assert "Successfully extracted cookies" in message
