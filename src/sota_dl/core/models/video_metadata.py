from pydantic import BaseModel


class VideoMetadata(BaseModel):
    """Represents the metadata of a media item."""

    title: str
    url: str
    format: str | None = None
    duration: int | None = None

    def get_info(self) -> str:
        """
        Returns a string representation of the media information.

        Returns:
            A formatted string containing the title and duration.
        """
        return f"{self.title} ({self.duration or 'unknown'}s)"
