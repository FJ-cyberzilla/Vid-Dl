"""Orchestration service for managing download tasks."""

import os
from typing import List
from core.protocols import Downloader


class DownloadService:
    """Service to orchestrate download operations."""

    def __init__(self, downloader: Downloader):
        self.downloader = downloader

    def process_target(self, target: str) -> None:
        """Processes a target (URL or batch file) and delegates to the downloader."""
        target = target.strip()

        if os.path.isfile(target) and target.endswith(".txt"):
            urls = self._parse_batch_file(target)
        else:
            urls = [target]

        for url in urls:
            self.downloader.execute(url)

    def _parse_batch_file(self, file_path: str) -> List[str]:
        """Parses URLs from a batch text file."""
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            raise ValueError("The batch file is empty or contains no valid URLs.")
        return urls
