"""Service for resolving download targets from various inputs."""

import os
from pathlib import Path


class TargetResolver:
    """Handles parsing and validation of download targets."""

    @staticmethod
    def resolve(target: str) -> list[str]:
        """Resolves a target URL or batch file path into a list of URLs."""
        target = target.strip()
        if os.path.isfile(target) and target.lower().endswith((".txt", ".lst")):
            return TargetResolver._parse_batch_file(target)
        return [target]

    @staticmethod
    def _parse_batch_file(file_path: str) -> list[str]:
        urls = []
        path = Path(file_path)
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
        if not urls:
            raise ValueError(f"Batch file '{file_path}' contains no valid URLs.")
        return urls
