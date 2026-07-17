# SOTA Media Extractor
A lightweight, high-performance, and modular media downloader optimized for Termux and Android environments.

## Architecture Philosophy
SOTA (State of the Art) rejects the "bloatware" approach. By utilizing a clean, modular structure following SOLID principles, it minimizes the system footprint, reduces error rates, and ensures that maintenance is surgical—not destructive. 

* **Core:** `yt-dlp` (The industry standard for extraction)
* **UI:** `rich` (For elegant, real-time terminal feedback)
* **Design:** Decoupled UI, Service/Core Logic, and Configuration.

## Key Features
* **Structural Integrity:** Follows modern Python design patterns (SRP, DIP) for high testability.
* **Orchestrated Workflows:** Uses a dedicated `DownloadService` to handle batch processing, decoupling it from the downloader engine.
* **Zero-Cookie OAuth:** Bypasses legacy login issues via external `cookies.txt` handling.
* **Smart Routing:** Auto-detects Android storage vs. local Termux paths with side-effect-free path resolution.
* **Dynamic Batching:** Supports single URLs, Playlists, and local `.txt` file parsing.
* **Quality Control:** On-the-fly selection for bitrate/resolution.

## Installation
1. Ensure `ffmpeg` is installed: `pkg install ffmpeg python`
2. Install dependencies: `pip install -e .`
3. Launch: `sota`

## Usage
* **Single URL:** Paste link when prompted.
* **Batch/Playlist:** Paste the URL or the full path to a `.txt` file containing links.
* **Format:** Select resolution or bitrate from the interactive menu.

## Developer Tips
* **Extensibility:** The `core/protocols.py` defines clear interfaces, making it easy to swap backends or extend UI reporting.
* **Batch Files (`learn.txt`):** Keep a text file in `~/Vid-Dl` with one URL per line. When prompted for a URL, simply type `learn.txt`.
* **Custom Paths:** You can customize storage paths in `config/settings.py`. To include daily subfolders, inject logic into `get_download_path()`.
