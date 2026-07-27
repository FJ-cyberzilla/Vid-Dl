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

APP_NAME  := $(BOLD)$(CYAN)SOTA Vid-Dl$(RESET) $(DIM)v3.0.1$(RESET)
BRAND     := $(BOLD)$(VIOLET)FJ™ Cyberzilla Systems$(RESET)

.DEFAULT_GOAL := help
.PHONY: help install dev update run diagnose lint format clean test coverage build menu \
        install-completion

# ==============================================================================
# TARGETS
# ==============================================================================

##@ 🚀 Execution
run: ## Launch the application
	@printf " $(ICON_NODE) $(CYAN)Launching $(APP_NAME)...$(RESET)\n\n"
	@PYTHONPATH=src uv run python -m sota_dl.main

menu: ## Launch interactive command selector (fzf / select fallback)
	@if command -v fzf >/dev/null 2>&1; then \
		target=$$(awk '/^[a-zA-Z_-]+:.*?##/ { sub(":.*##", " —"); print }' $(MAKEFILE_LIST) | \
			fzf --ansi \
			    --header="❖ SOTA Downloader — Target Chooser" \
			    --color="fg+:255,bg+:236,header:51,info:141,pointer:198,prompt:51" \
			    --prompt="❯ Execute target: " \
			    --height=45% --layout=reverse --border=rounded | \
			awk '{print $$1}'); \
		if [ -n "$$target" ]; then \
			printf "\n $(ICON_NODE) $(CYAN)Executing target: $(BOLD)%s$(RESET)\n\n" "$$target"; \
			$(MAKE) $$target; \
		fi; \
	else \
		printf " $(ICON_WARN) $(AMBER)fzf not installed. Using fallback menu:$(RESET)\n\n"; \
		PS3="❯ Select target number: "; \
		targets=($$(grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | cut -d: -f1)); \
		select target in "$${targets[@]}" "Quit"; do \
			if [ "$$target" = "Quit" ] || [ -z "$$target" ]; then break; fi; \
			$(MAKE) $$target; \
			break; \
		done; \
	fi

##@ 📦 Environment & Setup
install: ## Install main dependencies (production)
	@printf " $(ICON_NODE) $(CYAN)Installing production dependencies...$(RESET)\n"
	@uv sync --no-dev
	@uv pip install -e .
	@printf " $(ICON_OK) $(EMERALD)Production installation complete.$(RESET)\n"

dev: ## Install development dependencies
	@printf " $(ICON_NODE) $(CYAN)Installing development dependencies...$(RESET)\n"
	@uv sync
	@uv pip install -e .
	@printf " $(ICON_OK) $(EMERALD)Development installation complete.$(RESET)\n"

update: ## Upgrade locked dependencies (uv lock --upgrade)
	@printf " $(ICON_NODE) $(CYAN)Updating locked dependencies...$(RESET)\n"
	@uv lock --upgrade
	@uv sync
	@printf " $(ICON_OK) $(EMERALD)Dependencies successfully updated.$(RESET)\n"

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
diagnose: ## Run environment and dependency compatibility check
	@printf "\n $(BOLD)$(CYAN)┌── Environment Diagnostic Dashboard ─────────────────────────┐$(RESET)\n"
	@printf " $(CYAN)│$(RESET) Core Dependencies : "
	@uv run python -c "import yt_dlp, rich, mutagen, pydantic, tenacity, requests" 2>/dev/null \
		&& printf "$(ICON_OK) $(EMERALD)All required modules loaded$(RESET)\n" \
		|| printf "$(ICON_FAIL) $(ROSE)Missing required modules$(RESET)\n"
	@printf " $(CYAN)│$(RESET) Optional psutil   : "
	@uv run python -c "import importlib.util; exit(0 if importlib.util.find_spec('psutil') else 1)" 2>/dev/null \
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
	@uv run ruff check .

format: ## Format codebase with Ruff
	@printf " $(ICON_NODE) $(CYAN)Formatting files with Ruff...$(RESET)\n"
	@uv run ruff format .

##@ 🧪 Test & Build
test: ## Run test suite with inline coverage
	@printf " $(ICON_NODE) $(CYAN)Running tests...$(RESET)\n"
	@PYTHONPATH=src uv run pytest --cov --cov-report=html --cov-report=term

coverage: ## View terminal coverage summary
	@printf "\n $(BOLD)$(CYAN)── Coverage Report Summary ────────────────────────────────────$(RESET)\n"
	@if [ -f htmlcov/index.html ]; then \
		PYTHONPATH=src uv run pytest --cov --cov-report=term | tail -n 20; \
		printf "\n $(ICON_WARN) $(AMBER)Full HTML Report:$(RESET) $(DIM)$(PWD)/htmlcov/index.html$(RESET)\n\n"; \
	else \
		printf " $(ICON_FAIL) $(ROSE)Report missing. Run $(BOLD)make test$(RESET) $(ROSE)first.$(RESET)\n\n"; \
	fi

build: ## Build distribution packages
	@printf " $(ICON_NODE) $(CYAN)Building package distribution...$(RESET)\n"
	@uv build
	@printf " $(ICON_OK) $(EMERALD)Package built in $(WHITE)dist/$(RESET)\n"

clean: ## Purge caches, build artifacts, and coverage data
	@printf " $(ICON_NODE) $(CYAN)Cleaning temporary files and build artifacts...$(RESET)\n"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
	@rm -rf build/ dist/ *.egg-info/ .ruff_cache/ .pytest_cache/ .mypy_cache/ htmlcov/ .coverage
	@printf " $(ICON_OK) $(EMERALD)Workspace cleaned.$(RESET)\n"

##@ 💡 System Help
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
