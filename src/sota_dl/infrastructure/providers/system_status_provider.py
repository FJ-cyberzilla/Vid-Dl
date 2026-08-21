
from sota_dl.core.models.system_status import SystemStatus
from sota_dl.config.settings import settings

class SystemStatusProviderImpl:
    def get_status(self) -> SystemStatus:
        # Simple check for DRM mode (if cryptography is importable)
        drm_mode = "Local"
        try:
            import cryptography  # noqa: F401
        except ImportError:
            drm_mode = "Remote"
            
        firebase_status = "Configured" if settings.FIREBASE_DRM_ENDPOINT else "Not Configured"
        
        return SystemStatus(
            local_storage_path=settings.get_download_path(),
            cookies_path=settings.COOKIES_PATH,
            firebase_status=firebase_status,
            firebase_endpoint=settings.FIREBASE_DRM_ENDPOINT or "N/A",
            drm_mode=drm_mode
        )
