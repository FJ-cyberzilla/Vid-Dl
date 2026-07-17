"""Core yt-dlp execution and configuration module."""

import os
from typing import Optional

import yt_dlp
from config.settings import get_download_path
from config.colors import THEME
from ui.progress_bars import get_sota_progress
from core.protocols import ProgressReporter


class DownloadError(Exception):
    """Custom exception for download-related failures."""


class SOTADownloadManager:
    """Implementation of the Downloader protocol using yt-dlp."""

    def __init__(
        self,
        is_audio: bool = False,
        quality: str = "best",
        progress_ui: Optional[ProgressReporter] = None,
    ):
        self.is_audio = is_audio
        self.quality = quality
        self.output_path = get_download_path()
        os.makedirs(self.output_path, exist_ok=True)
        self.progress_ui = progress_ui or get_sota_progress()
        self.task_id: Optional[int] = None

    def _progress_hook(self, d: dict):
        """Routes yt-dlp progress directly into the Rich UI."""
        if self.task_id is None:
            return

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)

            filename = d.get("filename", "Media File")
            clean_title = os.path.basename(filename).rsplit(".", 1)[0][:40]

            self.progress_ui.update(
                self.task_id,
                description=f"[{THEME}]{clean_title}...",
                total=total if total > 0 else None,
                completed=downloaded,
            )
        elif d["status"] == "finished":
            self.progress_ui.update(
                self.task_id, description=f"[{THEME}]Processing metadata & merging..."
            )

    def _build_options(self) -> dict:
        """Constructs the SOTA download configuration based on requested quality."""
        opts = {
            "outtmpl": f"{self.output_path}/%(title)s.%(ext)s",
            "embedthumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "yes_playlist": True,
            "progress_hooks": [self._progress_hook],
        }

        # Check for cookies file to prevent non-existent path warnings
        if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0:
            opts["cookiefile"] = "cookies.txt"

        if self.is_audio:
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": self.quality,
                        },
                        {"key": "FFmpegMetadata", "add_metadata": True},
                        {"key": "EmbedThumbnail"},
                    ],
                }
            )
        else:
            # Let FFmpeg automatically handle non-mp4 source streams and merge them cleanly
            if self.quality == "best":
                video_format = "bestvideo+bestaudio/best"
            else:
                video_format = f"bestvideo[height<={self.quality}]+bestaudio/best"

            opts.update(
                {
                    "format": video_format,
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {"key": "FFmpegMetadata", "add_metadata": True},
                        {"key": "EmbedThumbnail"},
                    ],
                }
            )
        return opts

    def execute(self, target: str) -> None:
        """Initiates the extraction flow for a single URL."""
        opts = self._build_options()

        with self.progress_ui:
            self.task_id = self.progress_ui.add_task(
                "Initializing Download Engine...", total=None
            )
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([target])
