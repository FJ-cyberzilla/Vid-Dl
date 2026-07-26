import pytest
from unittest.mock import MagicMock, patch
from infrastructure.network import (
    NetworkManager,
    InvalidURLError,
)
from requests.exceptions import RequestException


@pytest.fixture
def network_manager() -> NetworkManager:
    return NetworkManager()


def test_validate_url(network_manager: NetworkManager) -> None:
    # Valid URLs
    network_manager._validate_url("https://example.com")
    network_manager._validate_url("http://example.com")

    # Invalid URLs
    with pytest.raises(InvalidURLError):
        network_manager._validate_url("ftp://example.com")
    with pytest.raises(InvalidURLError):
        network_manager._validate_url("")
    with pytest.raises(InvalidURLError):
        network_manager._validate_url("not-a-url")


def test_check_url_invalid(network_manager: NetworkManager) -> None:
    assert network_manager.check_url("ftp://invalid") is False
    assert network_manager.check_url("") is False


@patch("requests.Session.head")
def test_check_url_success(
    mock_head: MagicMock, network_manager: NetworkManager
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_head.return_value = mock_response

    assert network_manager.check_url("https://example.com") is True
    mock_head.assert_called_once()


@patch("requests.Session.head")
def test_check_url_failure(
    mock_head: MagicMock, network_manager: NetworkManager
) -> None:
    mock_head.side_effect = RequestException("Network error")

    assert network_manager.check_url("https://example.com") is False
    mock_head.assert_called_once()
