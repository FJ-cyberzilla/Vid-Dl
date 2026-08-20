# ==============================================================================
#  SOTA Downloader — Makefile
#  FJ™ Cybertronic Systems MMXXVI
# ==============================================================================

# ----- Modern 256-Color & Typography Palette -----
CYAN    := \033[38;5;51m
VIOLET  := \033[38;5;141m
AMBER   := \033[38;5;214m
EMERALD := \033[38;5;48m
ROSE    := \033[38;5;198m
GRAY    := \033[38;5;243m
WHITE   := \033[38;5;255m
BOLD    := \033[1m
DIM     := \033[2m
RESET   := \033[0m

# ----- UI Badges & Status Icons -----
ICON_OK   := $(EMERALD)✔$(RESET)
ICON_FAIL := $(ROSE)✖$(RESET)
ICON_WARN := $(AMBER)⚡$(RESET)
ICON_NODE := $(CYAN)❖$(RESET)

APP_NAME  := $(BOLD)$(CYAN)SOTA Vid-Dl$(RESET) $(DIM)v2.0.0$(RESET)
BRAND     := $(BOLD)$(VIOLET)FJ™ Cyberzilla Systems$(RESET)

# ----- Smart System & Environment Detection -----
RAW_OS    := $(shell uname -s 2>/dev/null || echo Windows)
IS_TERMUX := $(if $(wildcard /data/data/com.termux),1,0)

IS_WSL := 0
WSL_VER := 0
ifeq ($(RAW_OS),Linux)
    ifneq ($(wildcard /proc/sys/fs/binfmt_misc/WSLInterop),)
        IS_WSL := 1
        WSL_VER := 2
    else ifneq ($(wildcard /proc/version),)
        ifneq ($(shell grep -i microsoft /proc/version),)
            IS_WSL := 1
            WSL_VER := 1
        endif
    endif
endif

DISTRO := unknown
ifeq ($(RAW_OS),Linux)
    ifneq ($(wildcard /etc/os-release),)
        DISTRO := $(shell . /etc/os-release && echo $$ID)
    endif
endif

.DEFAULT_GOAL := help
.PHONY: help install dev update run diagnose lint format clean test coverage build menu \
        install-completion sync about sys-info install-deps

# ==============================================================================
# TARGETS
# ==============================================================================

##@ 🚀 Execution
run: ## Launch the application
	@printf " $(ICON_NODE) $(CYAN)Launching $(APP_NAME)...$(RESET)\n\n"
	@PYTHONPATH=src python3 -m sota_dl.main

menu: ## Launch interactive command selector (fzf / select fallback)
	@bash -c 'if command -v fzf >/dev/null 2>&1; then \
		target=$$(awk "/^[a-zA-Z_-]+:.*?##/ { sub(/:.*##/, \" —\"); print }" $(MAKEFILE_LIST) | \
			fzf --ansi \
				--header="❖ SOTA Downloader — Target Chooser" \
				--color="fg+:220,bg+:141,header:51,info:141,pointer:198,prompt:51" \
				--prompt="❯ Execute target: " \
				--height=45% --layout=reverse --border=rounded | \
			awk "{print \$$1}"); \
		if [ -n "$$target" ]; then \
			printf "\n $(ICON_NODE) $(CYAN)Executing target: $(BOLD)%s$(RESET)\n\n" "$$target"; \
			$(MAKE) $$target; \
		fi; \
	else \
		printf " $(ICON_WARN) $(AMBER)fzf not installed. Using fallback menu:$(RESET)\n\n"; \
		PS3="❯ Select target number: "; \
		targets=($$(grep -E "^[a-zA-Z_-]+:.*?##" $(MAKEFILE_LIST) | cut -d: -f1)); \
		select target in "$${targets[@]}" "Quit"; do \
			if [ "$$target" = "Quit" ] || [ -z "$$target" ]; then break; fi; \
			$(MAKE) $$target; \
			break; \
		done; \
	fi'

##@ 📦 Environment & Setup
sys-info: ## Display detected OS and environment details
	@printf "\n $(BOLD)$(VIOLET)┌── System Environment Detection ──────────────────────────┐$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(MAGENTA)Raw OS / Kernel :$(RESET)  $(WHITE)$(RAW_OS)$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(MAGENTA)Termux Detected :$(RESET)  $(if $(filter 1,$(IS_TERMUX)),$(AMBER)$(BOLD)YES (Android Subsystem)$(RESET),$(WHITE)NO$(RESET))\n"
	@printf " $(VIOLET)│$(RESET)  $(MAGENTA)WSL Environment :$(RESET)  $(if $(filter 1,$(IS_WSL)),$(CYAN)$(BOLD)YES (WSL$(WSL_VER))$(RESET),$(WHITE)NO$(RESET))\n"
	@printf " $(VIOLET)│$(RESET)  $(MAGENTA)Linux Distro    :$(RESET)  $(WHITE)$(DISTRO)$(RESET)\n"
	@printf " $(BOLD)$(VIOLET)└──────────────────────────────────────────────────────────┘$(RESET)\n\n"

install-deps: sys-info ## Auto-install system level packages (FFmpeg, Python headers)
	@if [ "$(IS_TERMUX)" = "1" ]; then \
		printf " $(ICON_WARN) $(AMBER)Termux detected. Installing minimal binaries via pkg...$(RESET)\n"; \
		pkg update -y && pkg install -y python python-pip ffmpeg aria2 git; \
	elif [ "$(RAW_OS)" = "Darwin" ]; then \
		printf " $(ICON_NODE) $(CYAN)Installing macOS dependencies via Homebrew...$(RESET)\n"; \
		brew install python ffmpeg aria2 git; \
	elif [ "$(RAW_OS)" = "Linux" ]; then \
		printf " $(ICON_NODE) $(CYAN)Installing Linux dependencies ($(DISTRO)...)$(RESET)\n"; \
		if [ "$(DISTRO)" = "ubuntu" ] || [ "$(DISTRO)" = "debian" ]; then \
			sudo apt-get update && sudo apt-get install -y build-essential python3-dev python3-pip ffmpeg aria2 git; \
		elif [ "$(DISTRO)" = "fedora" ] || [ "$(DISTRO)" = "rhel" ]; then \
			sudo dnf groupinstall -y "Development Tools" && sudo dnf install -y python3-devel python3-pip ffmpeg aria2 git; \
		elif [ "$(DISTRO)" = "arch" ]; then \
			sudo pacman -Sy --noconfirm base-devel python-pip ffmpeg aria2 git; \
		fi; \
	elif [ "$(RAW_OS)" = "Windows" ]; then \
		printf " $(ICON_WARN) $(AMBER)Windows native detected. Use PowerShell with winget:$(RESET)\n"; \
		printf " $(WHITE)winget install Python.Python.3.11 ; winget install Gyan.FFmpeg$(RESET)\n"; \
	fi

install: sys-info ## Install application dependencies with smart environment fallbacks
	@if [ "$(IS_TERMUX)" = "1" ]; then \
		printf " $(ICON_WARN) $(AMBER)Termux constraint mode active. Bypassing heavy builds...$(RESET)\n"; \
		if command -v uv >/dev/null 2>&1; then \
			uv pip install --only-binary=:all: -e . || pip install --only-binary=:all: -e .; \
		else \
			pip install --upgrade pip; \
			pip install --only-binary=:all: -e . || pip install cryptography wheel -e .; \
		fi; \
		printf " $(ICON_OK) $(EMERALD)Termux installation completed successfully.$(RESET)\n"; \
	else \
		printf " $(ICON_NODE) $(CYAN)Installing full production dependencies via uv...$(RESET)\n"; \
		uv sync --no-dev && uv pip install -e .; \
		printf " $(ICON_OK) $(EMERALD)Production installation complete.$(RESET)\n"; \
	fi

dev: sys-info ## Install development dependencies
	@if [ "$(IS_TERMUX)" = "1" ]; then \
		printf " $(ICON_WARN) $(AMBER)Termux detected: Heavy dev tools skipped for stability.$(RESET)\n"; \
		pip install -e .; \
	else \
		printf " $(ICON_NODE) $(CYAN)Installing development dependencies...$(RESET)\n"; \
		uv sync && uv pip install -e .; \
		printf " $(ICON_OK) $(EMERALD)Development installation complete.$(RESET)\n"; \
	fi

update: ## Upgrade locked dependencies (uv lock --upgrade)
	@printf " $(ICON_NODE) $(CYAN)Updating locked dependencies...$(RESET)\n"
	@uv lock --upgrade
	@uv sync
	@printf " $(ICON_OK) $(EMERALD)Dependencies successfully updated.$(RESET)\n"

sync: ## Synchronize environment with lockfile
	@printf " $(ICON_NODE) $(CYAN)Synchronizing environment...$(RESET)\n"
	@uv sync
	@printf " $(ICON_OK) $(EMERALD)Synchronization complete.$(RESET)\n"

install-completion: ## Auto-detect shell and install tab completion to .zshrc/.bashrc
	@shell_bin="$$(basename "$$SHELL")"; \
	if [ "$$shell_bin" = "zsh" ] || [ -f "$$HOME/.zshrc" ]; then \
		rc="$$HOME/.zshrc"; \
		marker="# --- SOTA Makefile Completion ---"; \
		if grep -q "$$marker" "$$rc" 2>/dev/null; then \
			printf " $(ICON_WARN) $(AMBER)Completion already installed in $(WHITE)$$rc$(RESET)\n"; \
		else \
			printf "\n$$marker\n_sota_make() {\n  if [[ -f Makefile ]]; then\n    local -a targets\n    targets=(\$${(f)\"$$(awk -F':.*?## ' '/^[a-zA-Z_-]+:.*?##/ {printf \"%s:%s\\\\n\", \$$1, \$$2}' Makefile)\"})\n    _describe -t make-targets 'make target' targets\n  fi\n}\ncompdef _sota_make make\n" >> "$$rc"; \
			printf " $(ICON_OK) $(EMERALD)Zsh completion installed to $(WHITE)$$rc$(RESET)\n"; \
			printf " $(ICON_NODE) Run $(BOLD)source $$rc$(RESET) to apply changes immediately.\n"; \
		fi; \
	elif [ "$$shell_bin" = "bash" ] || [ -f "$$HOME/.bashrc" ]; then \
		rc="$$HOME/.bashrc"; \
		marker="# --- SOTA Makefile Completion ---"; \
		if grep -q "$$marker" "$$rc" 2>/dev/null; then \
			printf " $(ICON_WARN) $(AMBER)Completion already installed in $(WHITE)$$rc$(RESET)\n"; \
		else \
			printf "\n$$marker\n_sota_make() {\n  local cur=\"\$${COMP_WORDS[COMP_CWORD]}\"\n  if [[ -f Makefile ]]; then\n    local targets=\$$(grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk -F':' '{print \$$1}')\n    COMPREPLY=( \$$(compgen -W \"\$${targets}\" -- \"\$${cur}\") )\n  fi\n}\ncomplete -F _sota_make make\n" >> "$$rc"; \
			printf " $(ICON_OK) $(EMERALD)Bash completion installed to $(WHITE)$$rc$(RESET)\n"; \
			printf " $(ICON_NODE) Run $(BOLD)source $$rc$(RESET) to apply changes immediately.\n"; \
		fi; \
	else \
		printf " $(ICON_FAIL) $(ROSE)Unable to detect .zshrc or .bashrc in $$HOME$(RESET)\n"; \
	fi

##@ 🔍 Quality & Diagnostics
diagnose: sys-info ## Run environment and dependency compatibility check
	@printf "\n $(BOLD)$(CYAN)┌── Environment Diagnostic Dashboard ─────────────────────────┐$(RESET)\n"
	@printf " $(CYAN)│$(RESET) Core Dependencies : "
	@python3 -c "import yt_dlp, rich, pydantic, tenacity, requests" 2>/dev/null \
		&& printf "$(ICON_OK) $(EMERALD)All required modules loaded$(RESET)\n" \
		|| printf "$(ICON_FAIL) $(ROSE)Missing required modules$(RESET)\n"
	@printf " $(CYAN)│$(RESET) Optional psutil   : "
	@python3 -c "import importlib.util; exit(0 if importlib.util.find_spec('psutil') else 1)" 2>/dev/null \
		&& printf "$(ICON_OK) $(EMERALD)Found$(RESET)\n" \
		|| printf "$(ICON_WARN) $(AMBER)Not found $(DIM)(using internal fallback)$(RESET)\n"
	@printf " $(CYAN)│$(RESET) FFmpeg Binary     : "
	@command -v ffmpeg >/dev/null 2>&1 \
		&& printf "$(ICON_OK) $(EMERALD)Found in PATH$(RESET)\n" \
		|| printf "$(ICON_FAIL) $(ROSE)Not found! $(AMBER)(Required for media processing)$(RESET)\n"
	@printf " $(CYAN)│$(RESET) Aria2c Binary    : "
	@command -v aria2c >/dev/null 2>&1 \
		&& printf "$(ICON_OK) $(EMERALD)Found in PATH$(RESET)\n" \
		|| printf "$(ICON_WARN) $(AMBER)Not found $(DIM)(optional)$(RESET)\n"
	@printf " $(BOLD)$(CYAN)└──────────────────────────────────────────────────────────────┘$(RESET)\n\n"

lint: ## Analyze code with Ruff
	@printf " $(ICON_NODE) $(CYAN)Checking code quality with Ruff...$(RESET)\n"
	@uv run ruff check . || ruff check .

format: ## Format codebase with Ruff
	@printf " $(ICON_NODE) $(CYAN)Formatting files with Ruff...$(RESET)\n"
	@uv run ruff format . || ruff format .

##@ 🧪 Test & Build
test: ## Run test suite with inline coverage
	@printf " $(ICON_NODE) $(CYAN)Running tests...$(RESET)\n"
	@PYTHONPATH=src pytest --cov --cov-report=html --cov-report=term || PYTHONPATH=src uv run pytest --cov --cov-report=html --cov-report=term

coverage: ## View terminal coverage summary
	@printf "\n $(BOLD)$(CYAN)── Coverage Report Summary ────────────────────────────────────$(RESET)\n"
	@if [ -f htmlcov/index.html ]; then \
		PYTHONPATH=src pytest --cov --cov-report=term | tail -n 20; \
		printf "\n $(ICON_WARN) $(AMBER)Full HTML Report:$(RESET) $(DIM)$(PWD)/htmlcov/index.html$(RESET)\n\n"; \
	else \
		printf " $(ICON_FAIL) $(ROSE)Report missing. Run $(BOLD)make test$(RESET) $(ROSE)first.$(RESET)\n\n"; \
	fi

build: ## Build distribution packages
	@printf " $(ICON_NODE) $(CYAN)Building package distribution...$(RESET)\n"
	@uv build || python3 -m build
	@printf " $(ICON_OK) $(EMERALD)Package built in $(WHITE)dist/$(RESET)\n"

clean: ## Purge caches, build artifacts, and coverage data
	@printf " $(ICON_NODE) $(CYAN)Cleaning temporary files and build artifacts...$(RESET)\n"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
	@rm -rf build/ dist/ *.egg-info/ .ruff_cache/ .pytest_cache/ .mypy_cache/ htmlcov/ .coverage
	@printf " $(ICON_OK) $(EMERALD)Workspace cleaned.$(RESET)\n"

##@ 💡 System Help
about: ## Display information about the application, architecture, and developers
	@printf "\n"
	@printf " $(VIOLET)┌────────────────────────────────────────────────────────────────────────────┐$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(BOLD)$(CYAN)SOTA Vid-Dl — System Infographic$(RESET)                                          $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)├────────────────────────────────────────────────────────────────────────────┤$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(BOLD)$(AMBER)Core Capabilities:$(RESET)                                                         $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(DIM)•$(RESET) $(WHITE)Multi-threaded async extraction of high-grade audio and video streams.$(RESET) $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(DIM)•$(RESET) $(WHITE)Automated OAuth device flow authentication for uninterrupted sessions.$(RESET)  $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(DIM)•$(RESET) $(WHITE)Smart, zero-trust caching layer optimized for mobile file systems.$(RESET)     $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(DIM)•$(RESET) $(WHITE)Seamless integration with multi-backend networks (yt-dlp & aria2c).$(RESET)    $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)                                                                            $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(BOLD)$(EMERALD)Architecture Overview:$(RESET)                                                    $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(WHITE)  [ CLI Layer ]   ──>   [ Orchestrator ]   ──>   [ Downloader/Service ]   $(RESET)$(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)         │                     │                         │                  $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)         ▼                     ▼                         ▼                  $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  [ Rich UI View ]       [ Event Bus ]         [ Adapters (yt-dlp, ffmpeg) ]$(RESET)$(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)                                                                            $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(BOLD)$(ROSE)Development & Engineering:$(RESET)                                                 $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(WHITE)Built with Python 3.13+, asyncio, Pydantic, and rich layouts.$(RESET)              $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(WHITE)Strict PEP 8, Ruff compliance, and robust SOLID design principles.$(RESET)         $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)                                                                            $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)│$(RESET)  $(WHITE)Engineering & Architecture by $(RESET)$(BRAND)                                $(VIOLET)│$(RESET)\n"
	@printf " $(VIOLET)└────────────────────────────────────────────────────────────────────────────┘$(RESET)\n"
	@printf "\n"

help: ## Display this categorized command overview
	@printf "\n"
	@printf " $(CYAN) _______ _______ _______ _______      ___ ___ __     __        _____  __ $(RESET)\n"
	@printf " $(CYAN)|     __|       |_     _|   _   |    |   |   |__|.--|  |______|     \|  |$(RESET)\n"
	@printf " $(CYAN)|__     |   -   | |   | |       |    |   |   |  ||  _  |______|  --  |  |$(RESET)\n"
	@printf " $(CYAN)|_______|_______| |___| |___|___|     \_____/|__||_____|      |_____/|__|$(RESET)\n"
	@printf "\n"
	@printf " $(CYAN)══════════════════════════════════════════════════════════════════════════════$(RESET)\n"
	@printf "  $(APP_NAME)  $(GRAY)•$(RESET)  $(BRAND)\n"
	@printf " $(CYAN)══════════════════════════════════════════════════════════════════════════════$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} \
		/^##@/ { printf "\n\033[1;38;5;51m%s\033[0m\n", substr($$0, 5) } \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[38;5;141m%-18s\033[0m \033[38;5;243m❯\033[0m \033[38;5;255m%s\033[0m\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\n $(GRAY)──────────────────────────────────────────────────────────────────────────────$(RESET)\n\n"
