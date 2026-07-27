from pydantic import BaseModel


class VideoMetadata(BaseModel):
    title: str
    url: str
    format: str | None = None
    duration: int | None = None
