SOTA Vid-Dl v2.0.0
High-Performance, Modular, and Resilient Media Extractor for Termux & Android > Maintained by FJ-Cyberzilla • FJ™ Cybertronic Systems

🚀 Overview
SOTA Vid-Dl rejects the "bloatware" approach common in media download utilities. By utilizing a clean, modular structure following PEP 517 src/ layout and SOLID principles, it minimizes the system footprint, reduces error rates, and ensures that maintenance is surgical—not destructive. Optimized specifically for mobile environments like Termux on Android.

🏛️ Architecture Philosophy
- Domain Boundary Refactoring: Enforced strict separation of concerns across layers (CLI Layer → Orchestrator → Service Layer → Repository/Adapter).
- Resilience: Implemented exponential backoff retries via tenacity to handle transient network errors.
- Composition: Orchestration of lifecycle via DownloadController (pause/resume/cancel).
- Validation: Strict runtime data integrity using Pydantic.
- Observability: Structured logging via structlog.

📂 Project Directory Structure
├── Makefile
├── pyproject.toml
├── README.md
├── src/
│   └── sota_dl/
│       ├── config/
│       ├── core/
│       ├── infrastructure/
│       ├── ui/
│       └── utils/
├── tests/
│   ├── config/
│   ├── core/
│   ├── infrastructure/
│   ├── integration/
│   ├── ui/
│   └── utils/
└── docs/

⚙️ Core Components
- sota_dl/core/: Business logic (controller, download_service, models).
- sota_dl/infrastructure/: Adapters (yt-dlp, aria2c, ffmpeg), telemetry, system monitoring.
- sota_dl/ui/: Interactive CLI rendering.
- sota_dl/config/: Application settings and environment management.
- sota_dl.support/: Helper functions and utilities.

🛠️ Makefile Commands
SOTA Vid-Dl includes a streamlined Makefile for developer operations:

make <command>

Command | Description
--- | ---
build | Build distributable package
clean | Remove temporary files, caches, and test outputs
coverage | Show code coverage summary directly in the terminal
dev | Install application with full development extras
diagnose | Run system compatibility and tool check
format | Run ruff code formatter
help | Show built-in help message
install | Install core production dependencies
lint | Run ruff linter checks
run | Launch the application CLI
sys-info | Display detected OS and environment details
test | Run the complete test suite with coverage report
update | Update dependencies (uv lock --upgrade)

### 🖥️ Smart System & Environment Detection
SOTA Vid-Dl utilizes an advanced Makefile-based detection system to configure the environment automatically. It supports:
- **Termux (Android):** Optimized for low-footprint installation.
- **macOS:** Automated Homebrew dependency resolution.
- **Linux:** Multi-distro detection (Debian, Fedora, Arch) with native package management.
- **Windows:** Detects PowerShell capabilities to automatically install dependencies via `winget` (Python, FFmpeg, aria2).

Run `make sys-info` to view the currently detected environment configuration.

💡 Usage & Tips
- Single URL: Paste any supported media link when prompted by the CLI.
- Batch Files: Maintain a text file with one URL per line. When prompted for a URL, provide the path to the text file to trigger batch processing.
- Cookies: Place your cookies.txt in a configured secure location to bypass authentication roadblocks.
- Auto-Fallback: The system automatically falls back to the best available quality stream.

--- SOTA Vid-Dl v2.0.0 | FJ™ Cyberzilla ---

## ⚠️ Supported Platforms & Policy
SOTA Vid-Dl is designed for optimal performance on mobile-first environments (specifically Termux on Android) and general Linux environments.

**Strict Unsupported Platforms & Browsers:**
- **Apple/macOS:** This project does not support Apple operating systems or devices.
- **Safari Browser:** We do not support the Safari browser.

Attempting installation on these platforms will trigger a critical policy violation warning and terminate the installation process.

📚 Documentation
For detailed usage, configuration, and architecture details, refer to the [User Guide](docs/userguide.md).

---
## 🚫 Policy: No AI Training or Automated Analysis
This project and all associated documentation are provided for human use only. **Automated scraping, crawling, or analysis of this codebase for the purpose of training AI models or for data collection by automated bots is explicitly prohibited.**
---
