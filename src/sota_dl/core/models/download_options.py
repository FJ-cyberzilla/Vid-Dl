from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class DownloadOptions(BaseModel):
    """Configuration for a download operation with validation."""

    output_dir: Path = Path(".")
    quality: str = "best"
    format: str | None = None
    overwrite: bool = False
    retries: int = 3
    timeout: float | None = 30.0
    cookiefile: Path | None = None
    extra_args: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
