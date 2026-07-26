"""Standardizes application directories using platformdirs."""

import os
from pathlib import Path
from platformdirs import PlatformDirs

# Define app name and author for platformdirs
APP_NAME = "Vid-Dl"
APP_AUTHOR = "FJ_Cyberzilla"

dirs = PlatformDirs(APP_NAME, APP_AUTHOR)

# Define standard paths
CONFIG_DIR = Path(dirs.user_config_dir)
DATA_DIR = Path(dirs.user_data_dir)
LOG_DIR = Path(dirs.user_log_dir)
DOWNLOAD_DIR = Path(os.path.expanduser("~/Downloads/VideoDL"))

# Ensure directories exist
for directory in [CONFIG_DIR, DATA_DIR, LOG_DIR, DOWNLOAD_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
