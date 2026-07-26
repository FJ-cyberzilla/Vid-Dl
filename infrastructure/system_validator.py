"""Validates system environment requirements."""

import shutil
import sys
import logging

logger = logging.getLogger(__name__)

def verify_system_dependencies() -> None:
    """Verifies that mandatory system binaries are installed."""
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if not shutil.which("aria2c"):
        missing.append("aria2c")

    if missing:
        msg = f"Error: Missing required system binaries: {', '.join(missing)}"
        logger.error(msg)
        print(f"❌ {msg}")
        print("Please install the required binaries.")
        sys.exit(1)
