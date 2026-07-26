Sota Vid-Dl v3.0.1
​High-Performance, Modular, and Resilient Media Extractor for Termux & Android > Maintained by FJ-Cyberzilla • FJ™ Cybertronic Systems
​🚀 Overview
​Sota Vid-Dl rejects the "bloatware" approach common in media download utilities. By utilizing a clean, modular structure following SOLID principles, it minimizes the system footprint, reduces error rates, and ensures that maintenance is surgical—not destructive. Optimized specifically for mobile environments like Termux on Android.
​🏛️ Architecture Philosophy
​Strategy Pattern: Formalized DownloaderBackend protocol with support for multiple, fallible backends.
​Resilience: Implemented exponential backoff retries via tenacity to handle transient network errors.
​Composition: Orchestration of lifecycle via DownloadController (pause/resume/cancel) and execution via FallbackDownloader.
​Validation: Strict runtime data integrity using pydantic.
​📂 Project Directory Structure
├── Makefile
├── README.md
├── composition_root.py
├── config
│   ├── __init__.py
│   ├── colors.py
│   └── settings.py
├── cookies.txt
├── core
│   ├── __init__.py
│   ├── controller.py
│   ├── download_manager.py
│   ├── download_service.py
│   ├── fallback.py
│   └── protocols.py
├── infrastructure
│   ├── __init__.py
│   ├── adapters
│   │   ├── __init__.py
│   │   └── yt_dlp.py
│   ├── aria2c.py
│   ├── errors.py
│   ├── ffmpeg.py
│   ├── file_system.py
│   ├── network.py
│   ├── pybalt.py
│   ├── pywidevine.py
│   ├── system.py
│   ├── videodl.py
│   └── yt_dlp_wrapper.py
├── main.py
├── plan1.txt
├── pyproject.toml
├── structure.mmf
├── test_output
├── tests
│   ├── test_architecture.py
│   ├── test_controller.py
│   ├── test_download_manager.py
│   ├── test_download_service.py
│   ├── test_file_system.py
│   ├── test_network.py
│   ├── test_sota.py
│   ├── test_system.py
│   └── test_yt_dlp_wrapper.py
├── ui
│   ├── __init__.py
│   ├── banners.py
│   ├── menus.py
│   └── progress_bars.py
├── utils
│   ├── __init__.py
│   ├── helpers.py
│   └── validators.py
└── uv.lock

⚙️ Component Breakdown
​1. core/
​controller.py: Handles job lifecycle operations (pause, resume, cancel).
​download_manager.py: Orchestrates backend execution pools.
​download_service.py: Handles batch queue parsing and orchestration workflows.
​fallback.py: Manages automated sequential failover across download adapters.
​protocols.py: Defines strict type interfaces (DownloaderBackend) for modular extension.
​2. infrastructure/
​adapters/yt_dlp.py: Primary wrapper adapter for yt-dlp execution.
​aria2c.py, ffmpeg.py: External system tool orchestration bindings.
​file_system.py, network.py, system.py: Cross-platform path and OS utilities.
​pybalt.py, pywidevine.py, videodl.py: Specialized DRM and stream decryption adapters.
​3. ui/
​banners.py: CLI welcome banners and branding displays.
​menus.py: Interactive terminal selection menus.
​progress_bars.py: Real-time download progress renderers.
​4. utils/
​helpers.py: General helper routines.
​validators.py: Input sanitization and URL validation utilities.
​🛠️ Makefile Commands
​Sota Vid-Dl includes a streamlined Makefile for developer operations:

make <command>



CommandDescription
buildBuild distributable package
cleanRemove temporary files, caches, and test outputs
coverageShow code coverage summary directly in the terminal
devInstall application with full development extras
diagnoseRun system compatibility and tool check
formatRun ruff code formatter
helpShow built-in help message
installInstall core production dependencies
lintRun ruff linter checks
runLaunch the application CLI (main.py)
testRun the complete test suite with coverage report
updateUpdate dependencies (uv lock --upgrade)




💡 Usage & Tips
​Single URL: Paste any supported media link when prompted by the CLI.
​Batch Files (learn.txt): Maintain a text file with one URL per line inside your download directory (~/Vid-Dl). When prompted for a URL, simply type learn.txt to trigger batch processing.
​Zero-Cookie OAuth: Place your exported cookies.txt in the root workspace directory to bypass legacy authentication roadblocks.
​Auto-Fallback: If your target resolution or bitrate is unavailable, the system automatically falls back to the best available quality stream.
​--- SOTA Vid-Dl v3.0.1 | FJ™ Cyberzilla ---
