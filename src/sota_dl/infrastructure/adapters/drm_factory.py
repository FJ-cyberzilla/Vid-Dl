"""
Factory for DRM services.
Supports hybrid local/remote implementation based on environment capability.
"""

import json
import urllib.request
import asyncio
from pathlib import Path
from typing import Callable, Any
from sota_dl.core.protocols import DRMService
from sota_dl.infrastructure.extensions.pywidevine import create_drm_service
from sota_dl.config.settings import settings

class RemoteFirebaseDRMService:
    """Remote implementation of DRMService using Firebase Functions."""

    def __init__(self, api_endpoint: str) -> None:
        self.api_endpoint = api_endpoint

    async def adecrypt(
        self,
        url: str,
        output_path: Path,
        headers: dict[str, str] | None = None,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float | None = None,
    ) -> Path:
        """
        Sends the request to Firebase Function securely.
        """
        if not self.api_endpoint:
            raise ValueError("Firebase DRM endpoint is not configured.")

        # Prepare payload
        payload = {"url": url, "headers": headers or {}}
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            self.api_endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.ACCESS_TOKEN or ''}"
            },
            method="POST",
        )
        
        loop = asyncio.get_running_loop()

        def _request() -> bytes:
            with urllib.request.urlopen(req, timeout=timeout or settings.TIMEOUT) as response:
                if response.status != 200:
                    raise Exception(f"Remote DRM failed with status {response.status}")
                return response.read()

        try:
            result = await loop.run_in_executor(None, _request)
            response_data = json.loads(result.decode("utf-8"))
            
            final_path = Path(response_data["path"])
            if not final_path.exists():
                 raise FileNotFoundError(f"Decrypted file not found at {final_path}")
            
            return final_path
        except Exception as e:
            raise Exception(f"Remote DRM processing failed: {e}") from e


def get_best_drm_service(device_path: Path) -> DRMService:
    """
    Factory that returns the best available DRMService:
    1. Local implementation (if dependencies are installed).
    2. Remote implementation (fallback).
    """
    local_service = create_drm_service(device_path)
    if local_service:
        return local_service
    
    return RemoteFirebaseDRMService(api_endpoint=settings.FIREBASE_DRM_ENDPOINT)
