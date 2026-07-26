"""Structured crash reporting."""

import traceback
import datetime
from pathlib import Path
from infrastructure.app_dirs import LOG_DIR

def report_crash(exc: Exception) -> Path:
    """Captures stack trace and writes to a structured log file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    crash_file = LOG_DIR / f"crash-report-{timestamp}.txt"
    
    with open(crash_file, "w", encoding="utf-8") as f:
        f.write(f"Crash Report - {datetime.datetime.now()}\n")
        f.write("-" * 30 + "\n")
        f.write(f"Exception: {type(exc).__name__}: {exc}\n")
        f.write("-" * 30 + "\n")
        traceback.print_exc(file=f)
    
    return crash_file
