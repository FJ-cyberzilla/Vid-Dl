import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from sota_dl.infrastructure.adapters.drm_factory import (
    get_best_drm_service,
    RemoteFirebaseDRMService,
)
from sota_dl.core.protocols import DRMService


# Test that the factory returns RemoteFirebaseDRMService
# when local dependencies are missing
@patch("sota_dl.infrastructure.adapters.drm_factory.create_drm_service")
def test_get_best_drm_service_fallback(mock_create_drm):
    # Simulate missing dependencies
    mock_create_drm.return_value = None

    device_path = Path(tempfile.gettempdir()) / "dummy.wvd"
    service = get_best_drm_service(device_path)

    assert isinstance(service, RemoteFirebaseDRMService)
    mock_create_drm.assert_called_once_with(device_path)


# Test that the factory returns local implementation when available
@patch("sota_dl.infrastructure.adapters.drm_factory.create_drm_service")
def test_get_best_drm_service_local(mock_create_drm):
    # Simulate local service available
    mock_local_service = MagicMock(spec=DRMService)
    mock_create_drm.return_value = mock_local_service

    device_path = Path(tempfile.gettempdir()) / "dummy.wvd"
    service = get_best_drm_service(device_path)

    assert service == mock_local_service
    mock_create_drm.assert_called_once_with(device_path)


# Test RemoteFirebaseDRMService structure (simplified for network-less testing)
@pytest.mark.asyncio
async def test_remote_drm_service_structure():
    service = RemoteFirebaseDRMService(api_endpoint="https://test.endpoint")
    assert service.api_endpoint == "https://test.endpoint"
    # Basic check that the method exists and can be called
    assert hasattr(service, "adecrypt")
