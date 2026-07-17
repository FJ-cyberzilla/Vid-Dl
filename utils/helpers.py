"""System utility functions."""

import os


def clear_screen():
    """Clears the terminal safely across OS environments."""
    os.system("cls" if os.name == "nt" else "clear")
