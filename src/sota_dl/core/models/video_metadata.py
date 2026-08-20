from pydantic import BaseModel
from typing import TypedDict


# Define a more specific type for format entries if possible
class MediaFormat(TypedDict):
    """Represents a single media format."""

    format_id: str
    ext: str
    resolution: str
    filesize: int | None
    url: str


class VideoMetadata(BaseModel):
    """Represents the metadata of a media item."""

    title: str
    url: str  # Kept for compatibility, though 5.txt uses webpage_url
    video_id: str | None = None
    webpage_url: str | None = None
    format: str | None = None
    duration: int | None = None
    uploader: str | None = None
    view_count: int | None = None
    formats: list[MediaFormat] | None = None

    def get_info(self) -> str:
        """
        Returns a string representation of the media information.

        Returns:
            A formatted string containing the title and duration.
        """
        return f"{self.title} ({self.duration or 'unknown'}s)"
