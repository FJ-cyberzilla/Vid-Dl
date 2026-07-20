"""Adapter for yt-dlp execution."""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Callable
import yt_dlp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.settings import COOKIES_PATH
from core.protocols import DownloadOptions, DownloadResult, DownloadStatus

logger = logging.getLogger(__name__)

class YtDlpBackend:
    """Handles the configuration and execution of yt-dlp with robust retries."""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(yt_dlp.utils.DownloadError),
        reraise=True
    )
    def download(self, target: str, options: DownloadOptions, progress_hook: Callable) -> DownloadResult:
        ydl_opts = self._build_ydl_opts(options, progress_hook)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target])
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                file_path=self._guess_output_path(target, options),
                metadata={"target": target},
            )
        except yt_dlp.utils.DownloadError as e:
            # Handle specific format error
            if "Requested format is not available" in str(e):
                logger.warning("Format not available for %s. Retrying with 'best'.", target)
                ydl_opts["format"] = "best"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([target])
                return DownloadResult(
                    status=DownloadStatus.COMPLETED,
                    file_path=self._guess_output_path(target, options),
                    metadata={"target": target, "fallback": True},
                )
            raise e
        except Exception as e:
            logger.exception("Unexpected error for %s", target)
            return DownloadResult(status=DownloadStatus.FAILED, error=str(e), metadata={"target": target})

    def _build_ydl_opts(self, options: DownloadOptions, progress_hook: Callable) -> Dict[str, Any]:
        is_audio = options.format in ("mp3", "m4a", "aac", "flac", "opus", "vorbis")
        quality = options.quality
        
        ydl_opts = {
            "outtmpl": str(options.output_dir / "%(title)s.%(ext)s"),
            "embedthumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "yes_playlist": True,
            "progress_hooks": [progress_hook],
            "retries": options.retries,
            "timeout": options.timeout or 30.0,
        }
        
        cookie_source = options.cookiefile or COOKIES_PATH
        if cookie_source and os.path.exists(cookie_source) and os.path.getsize(cookie_source) > 0:
            ydl_opts["cookiefile"] = str(Path(cookie_source).absolute())
        
        if options.overwrite:
            ydl_opts["overwrites"] = True
            
        if is_audio:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": options.format or "mp3", "preferredquality": quality},
                    {"key": "FFmpegMetadata", "add_metadata": True},
                    {"key": "EmbedThumbnail"},
                ],
            })
        else:
            video_format = f"bestvideo[height<={quality}]+bestaudio/best" if quality != "best" else "bestvideo+bestaudio/best"
            ydl_opts.update({
                "format": video_format,
                "merge_output_format": "mp4",
                "postprocessors": [{"key": "FFmpegMetadata", "add_metadata": True}, {"key": "EmbedThumbnail"}],
            })
            
        extra = options.extra_args.copy()
        extra.pop("cookiefile", None)
        ydl_opts.update(extra)
        
        return ydl_opts

    def _guess_output_path(self, target: str, options: DownloadOptions) -> Path:
        safe_target = target.replace("/", "_").replace(":", "_")[:30]
        return options.output_dir / f"download_{safe_target}"
