from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SystemStatus:
    local_storage_path: Path
    cookies_path: Path
    firebase_status: str
    firebase_endpoint: str
    drm_mode: str
