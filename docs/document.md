Sota Vid-Dl v2.0.0 — Complete Technical
& User Documentation
High-Performance, Modular, and Resilient Media Extractor for Termux & Android
Maintained by FJ-Cyberzilla • FJ™ Cybertronic Systems
🚀 1. Overview & Vision
Sota Vid-Dl is a lightweight, resilient, enterprise-grade command-line media extraction utility
designed specifically for resource-constrained mobile environments like Termux on Android as
well as standard Linux platforms.
Unlike traditional "monolithic" downloaders that accumulate technical debt and bloat, Sota
Vid-Dl is built around strict software engineering principles (SOLID architecture, decoupling,
runtime data validation). It prioritizes surgical maintenance, high fault tolerance, and zero
bloat.
Key Highlights
● Mobile First: Optimized memory footprint and I/O efficiency tailored for Termux on
Android.
● SOLID Architecture: Modular design through abstract protocols and decoupling.
● Automated Fallback: Graceful failover between backends (e.g., yt-dlp, aria2c, custom
adapters).
● Resilient Networking: Built-in exponential backoff retries handling transient mobile
network drops.
● DRM & Stream Support: Extensible binding layer for specialized stream decryption and
tools.
🏛️ 2. Architectural Philosophy
Sota Vid-Dl's architecture guarantees high reliability and ease of extendability:
+---------------------------------------------------------------------
--+
| USER INTERFACE
|
| (CLI Menus / Progress Bars / Banners / Terminal)
|
+---------------------------------------------------------------------
--+
|
v
+---------------------------------------------------------------------
--+
| CORE ORCHESTRATION |
| [DownloadController] ----> [DownloadService] ---->
[DownloadManager] |
| (Lifecycle & Queue) (Batch Workflow) (Backend Pools)
|
+---------------------------------------------------------------------
--+
|
v
+---------------------------------------------------------------------
--+
| FALLBACK & RETRY LAYER
|
| [FallbackDownloader] (Tenacity)
|
+---------------------------------------------------------------------
--+
|
+--------------------------+--------------------------+
| | |
v v v
+---------------+ +---------------+
+---------------+
| yt-dlp Adap. | | aria2c Adapter| | Custom DRM/
|
| (Primary) | | (Multi-seg) | | Decrypt Adap.
|
+---------------+ +---------------+
+---------------+
Core Design Patterns & Principles
1. Strategy Pattern (DownloaderBackend Protocol) The core system does not depend on
concrete downloader implementations. Every backend implements a strict
DownloaderBackend interface defined in core/protocols.py, enabling hot-swapping or
adding new extractors without touching core logic.
2. Resilience & Exponential Backoff (tenacity) Mobile connections suffer frequent IP
changes and signal drops. Network requests and stream extractions utilize exponential
backoff strategies via tenacity to retry transient failures transparently.
3. Lifecycle Management (DownloadController) Operations such as Pause, Resume,
and Cancel are managed through dedicated command state controllers rather than
terminating processes abruptly.
4. Strict Runtime Validation (pydantic) Configuration settings, runtime parameters,
network outputs, and CLI options are validated at execution time using Pydantic schemas
to prevent silent crashes deep in execution pipelines. 📂 3. Directory & File Reference
Below is the complete project layout and function mapping:
├── Makefile # Developer CLI macro command runner
├── README.md # Quick project overview
├── composition_root.py # Dependency injection container &
bootstrap setup
├── config/
│ ├── __init__.py
│ ├── colors.py # Terminal color formatting constants
(ANSI)
│ └── settings.py # Pydantic global application settings
& paths
├── cookies.txt # Workspace OAuth/Session
authentication file
├── core/
│ ├── __init__.py
│ ├── controller.py # Job lifecycle execution & state
tracking
│ ├── download_manager.py # Backend execution pool manager
│ ├── download_service.py # Queue processing and batch
line-by-line parsing
│ ├── fallback.py # Automatic sequential backend failover
logic
│ └── protocols.py # Abstract protocols & interface
definitions
├── infrastructure/
│ ├── __init__.py
│ ├── adapters/
│ │ ├── __init__.py
│ │ └── yt_dlp.py # Primary yt-dlp execution wrapper
adapter
│ ├── aria2c.py # Multi-connection download engine
bindings
│ ├── errors.py # Domain-specific custom exceptions
│ ├── ffmpeg.py # Post-processing, merging & muxing
bindings
│ ├── file_system.py # Cross-platform safe path & storage
utilities
│ ├── network.py # HTTP session, connectivity & socket
checks
│ ├── pybalt.py # Stream decryption adapter
│ ├── pywidevine.py # Widevine DRM decryption wrapper
adapter
│ ├── system.py # Termux detection, OS signals,
subprocess handlers │ ├── videodl.py # Specialized direct video extraction
wrapper
│ └── yt_dlp_wrapper.py # Low-level process invocation for
yt-dlp
├── main.py # Main application CLI entrypoint
├── pyproject.toml # Project metadata, dependencies, and
tools config
├── structure.mmf # Visual MindMap/Flow diagram structure
file
├── ui/
│ ├── __init__.py
│ ├── banners.py # ASCII headers and branding UI
elements
│ ├── menus.py # Interactive CLI menus and prompt
builders
│ └── progress_bars.py # Terminal progress bars and download
speed meters
├── utils/
│ ├── __init__.py
│ ├── helpers.py # Time, byte formatting, and
sanitization utilities
│ └── validators.py # URL verification and regex path
sanitizers
└── uv.lock # Locked dependency manifest for uv
package manager
⚙️ 4. Component Deep-Dive
1. core/ (Orchestration & Business Logic)
● controller.py: Intercepts terminal control signals and maintains state machines for active
download jobs (PENDING, DOWNLOADING, PAUSED, FAILED, COMPLETED).
● fallback.py: If yt-dlp fails due to stream rate-limiting or anti-bot protections,
FallbackDownloader automatically delegates extraction tasks to secondary backends like
aria2c or videodl.
● protocols.py: Defines standard type signatures:
from typing import Protocol, Dict, Any
class DownloaderBackend(Protocol):
def download(self, url: str, options: Dict[str, Any]) -> bool:
...
def supports(self, url: str) -> bool:
... 2. infrastructure/ (Adapters & External Bindings)
● adapters/yt_dlp.py & yt_dlp_wrapper.py: Converts system domain models into yt-dlp
executable options, managing cookies, header injection, and output formatting.
● aria2c.py: Invokes aria2c with multi-segment socket pooling (-s 16 -x 16) for maximum
bandwidth saturation.
● ffmpeg.py: Manages video-audio stream merging (e.g., combining .m4a and .mp4 dash
tracks), subtitle embedding, and format conversion.
● pywidevine.py & pybalt.py: Adapters for handling protected streams where authorized
key exchanges or specific decryptors are necessary.
3. ui/ (Presentation Layer)
● Rendered using terminal-native ANSI colors and formatted text blocks. Uses minimal
dependencies to ensure zero lag inside Termux screens.
📥 5. Installation & Setup Guide
Termux (Android) Installation
1. Update Packages & Install System Prerequisites:
pkg update && pkg upgrade -y
pkg install python ffmpeg aria2 git rust clang -y
2. Set Up Storage Access:
termux-setup-storage
3. Clone & Setup Sota Vid-Dl:
git clone
[https://github.com/FJ-Cyberzilla/sota-vid-dl.git](https://github.
com/FJ-Cyberzilla/sota-vid-dl.git)
cd sota-vid-dl
4. Install Python Dependencies via uv or pip:
○ Using uv (Recommended for fast installs):
pip install uv
uv pip install -e .
○ Standard pip:
pip install -e .
💡 6. User Operations & Features
1. Interactive Execution Launch the interactive shell interface:
python main.py
# or using Makefile
make run
2. Downloading Options
● Single Target: Enter any direct media URL (YouTube, Vimeo, Twitter/X, TikTok, Rumble,
Custom HTTP streams, etc.) when prompted.
● Batch Processing (learn.txt): Create a text file containing multiple URLs (one per line)
inside your downloads workspace directory (~/Vid-Dl/learn.txt). When prompted for a URL
in the CLI, enter:
learn.txt
The system will parse learn.txt and process the queue sequentially with automatic failure
recovery.
3. Zero-Cookie OAuth Authentication
To bypass strict login blocks or download age-restricted/private media:
1. Export browser cookies from an authenticated session into Netscape format (cookies.txt).
2. Place cookies.txt in the root workspace directory of sota-vid-dl.
3. Sota Vid-Dl automatically detects, validates, and injects cookies.txt into outgoing backend
requests.
4. Automatic Stream Fallback
If requested 4K/1080p formats are unavailable or protected by non-standard codecs, Sota
Vid-Dl automatically selects the highest available matching bitrate/resolution stream without
aborting the process.
🛠️ 7. Developer API & Makefile Manual
The built-in Makefile streamlines developer tasks:
make <command>
Command Description
build Package the application into a standard
distributable wheel/tarball
clean Purge build artifacts, cache files
(__pycache__), and temporary test files
coverage Run test suite and print complete code
coverage directly in the terminal
dev Install the application in editable mode with full
development extra tools
diagnose Run system diagnostics (verifies Termux
compatibility, ffmpeg, aria2c binaries) Command Description
format Automatically format all Python files using ruff
format
help Output quick Makefile command help table
install Install core production dependencies
lint Execute ruff code linter checks for code style
and bugs
run Instantly launch the application CLI (main.py)
test Run all unit & architecture integration tests with
pytest
update Re-lock dependencies to their latest compatible
versions (uv lock --upgrade)
🧪 8. Testing & Quality Assurance
The codebase includes an extensive suite of architectural and unit tests located in tests/:
● test_architecture.py: Verifies SOLID boundary compliance and module separation.
● test_controller.py: Tests job cancellation, pause/resume state switches.
● test_fallback.py: Mocks primary backend failures to ensure fallbacks trigger cleanly.
● test_network.py: Mocks network dropouts and verifies tenacity exponential retry logic.
To execute the test suite:
make test
🔧 9. Troubleshooting & Common Fixes
Issue Cause Solution
Permission Error [Storage] Termux storage permission not
granted
Run termux-setup-storage and
allow access on Android
prompt.
FFmpeg bindings missing ffmpeg package not installed in
environment
Run pkg install ffmpeg in
Termux.
HTTP 429 Too Many Requests IP rate-limited by target media
server
Inject cookies.txt or enable
aria2c with randomized user
agents.
Slow merge speeds CPU bottleneck on low-end
Android device
Lower video stream resolution
or enable fast container copy in
settings.py. 📜 10. License & Maintenance
● Maintainer: FJ-Cyberzilla • FJ™ Cybertronic Systems
● Target Release: Sota Vid-Dl v2.0.0 (MMXXVI Edition)
● Design Paradigm: Modular, Resilient, Clean Code Architecture
