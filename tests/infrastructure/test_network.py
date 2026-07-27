import pytest
from unittest.mock import MagicMock, patch
from sota_dl.infrastructure.network import (
    NetworkManager,
    InvalidURLError,
)


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


@pytest.mark.asyncio
async def test_check_url_async_success(network_manager: NetworkManager) -> None:
    # Patch check_url as it's the method run in the executor by check_url_async
    with patch.object(network_manager, "check_url", return_value=True) as mock_check:
        result = await network_manager.check_url_async("https://example.com")
        assert result is True
        mock_check.assert_called_once_with("https://example.com")


def test_build_session() -> None:
    session = NetworkManager._build_session(
        proxy="http://proxy:8080", max_retries=5, user_agent="TestAgent"
    )
    assert session.headers["User-Agent"] == "TestAgent"
    assert session.proxies["http"] == "http://proxy:8080"
    # Verify retry adapter is mounted
    assert "http://" in session.adapters
    assert "https://" in session.adapters


@patch("requests.Session.get")
def test_get_speed_mbps_success(
    mock_get: MagicMock, network_manager: NetworkManager
) -> None:
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"a" * 1024]
    mock_get.return_value.__enter__.return_value = mock_response

    speed = network_manager.get_speed_mbps(duration=0.1)
    assert speed > 0
