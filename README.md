# SOTA Media Extractor
A lightweight, high-performance, and modular media downloader optimized for Termux and Android environments.

## Architecture Philosophy
SOTA (State of the Art) rejects the "bloatware" approach. By utilizing a clean, modular structure following SOLID principles, it minimizes the system footprint, reduces error rates, and ensures that maintenance is surgical—not destructive. 

* **Strategy Pattern:** Formalized `DownloaderBackend` protocol with support for multiple, fallible backends.
* **Resilience:** Implemented exponential backoff retries via `tenacity` to handle transient network errors.
* **Composition:** Orchestration of lifecycle via `DownloadController` (pause/resume/cancel) and execution via `FallbackDownloader`.
* **Validation:** Strict runtime data integrity using `pydantic`.

## Key Features
* **Structural Integrity:** Follows modern Python design patterns (SRP, DIP) for high testability.
* **Enterprise Resilience:** Fallback mechanism attempts multiple downloaders sequentially; auto-retries transient failures.
* **Orchestrated Workflows:** Uses a dedicated `DownloadService` to handle batch processing.
* **Zero-Cookie OAuth:** Bypasses legacy login issues via external `cookies.txt` handling.
* **Smart Routing:** Auto-detects Android storage vs. local Termux paths with side-effect-free path resolution.
* **Dynamic Batching:** Supports single URLs, Playlists, and local `.txt` file parsing.
* **Dry Run Support:** Toggle-able dry run for safe testing without filesystem impact.

## Installation
1. Ensure `ffmpeg` is installed: `pkg install ffmpeg python`
2. Install dependencies: `pip install -e .`
3. Launch: `sota`

## Usage
* **Single URL:** Paste link when prompted.
* **Batch/Playlist:** Paste the URL or the full path to a `.txt` file containing links.
* **Format:** Select resolution or bitrate from the interactive menu. In case of format unavailability, the system will automatically fall back to the best available quality.

## Developer Tips
* **Extensibility:** The `core/protocols.py` defines clear interfaces. New backends can be added by implementing `DownloaderBackend` and adding them to the `FallbackDownloader` in `core/download_manager.py`.
* **Architecture:** Components are strictly separated into `adapters` (execution), `controller` (lifecycle), and `fallback` (resilience).
* **Batch Files (`learn.txt`):** Keep a text file in `~/Vid-Dl` with one URL per line. When prompted for a URL, simply type `learn.txt`.
* **Custom Paths:** You can customize storage paths in `config/settings.py`. To include daily subfolders, inject logic into `get_download_path()`.
