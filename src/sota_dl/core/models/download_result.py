from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from sota_dl.core.domain_types import DownloadStatus


class DownloadResult(BaseModel):
    """Result of a download attempt with validation."""

    status: DownloadStatus
    file_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
