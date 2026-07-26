from pydantic import BaseModel, Field
from typing import Any
from enum import Enum
from pathlib import Path

class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DownloadOptions(BaseModel):
    """Configuration for a download operation with validation."""
    output_dir: Path = Field(default_factory=lambda: Path("."))
    quality: str = "best"
    format: str | None = None
    overwrite: bool = False
    retries: int = 3
    timeout: float | None = 30.0
    cookiefile: Path | None = None
    extra_args: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False

class DownloadResult(BaseModel):
    """Result of a download attempt with validation."""
    status: DownloadStatus
    file_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class VideoMetadata(BaseModel):
    title: str
    url: str
    format: str | None = None
    duration: int | None = None

class DownloadTask(BaseModel):
    task_id: str
    metadata: VideoMetadata
    status: DownloadStatus = DownloadStatus.PENDING
    save_path: str
    retry_count: int = 0
