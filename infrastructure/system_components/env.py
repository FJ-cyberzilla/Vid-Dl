"""Environment detection utilities."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def is_linux() -> bool:
    """Return ``True`` if running on Linux (including Android)."""
    return platform.system().lower() == "linux"


def is_android() -> bool:
    """
    Return ``True`` if running on Android.

    Checks several indicators: ``ANDROID_ROOT``, ``TERMUX_VERSION``, or
    Android‑specific build properties.
    """
    if not is_linux():
        return False
    if is_termux():
        return True
    if os.environ.get("ANDROID_ROOT"):
        return True
    return Path("/system/build.prop").exists()


def is_termux() -> bool:
    """Return ``True`` if running inside Termux."""
    return os.environ.get("TERMUX_VERSION") is not None


def get_environment_name() -> str:
    """Return a human‑readable environment name."""
    if is_termux():
        return "Termux (Android)"
    if is_android():
        return "Android"
    system = platform.system()
    if system == "Linux":
        return "Linux"
    return system


def get_os() -> str:
    """Return the operating system name (e.g. 'Linux', 'Windows')."""
    return platform.system()


def get_os_version() -> str:
    """Return OS version string."""
    return platform.version()


def get_architecture() -> str:
    """Return machine architecture (e.g. 'x86_64', 'aarch64')."""
    return platform.machine()


def get_python_version() -> str:
    """Return the Python version string."""
    return platform.python_version()


def get_hostname() -> str:
    """Return the system hostname."""
    return platform.node()
