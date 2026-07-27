from pydantic import BaseModel
from sota_dl.core.types import DownloadStatus
from sota_dl.core.models.video_metadata import VideoMetadata


class DownloadTask(BaseModel):
    task_id: str
    metadata: VideoMetadata
    status: DownloadStatus = DownloadStatus.PENDING
    save_path: str
    retry_count: int = 0
