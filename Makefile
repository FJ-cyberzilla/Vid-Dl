# SOTA Downloader — Makefile
# FJ™ Cybertronic Systems
# Refactored for cross‑platform robustness and modern tooling.

# ----- aesthetics -----
BOLD   := $(shell tput bold 2>/dev/null || printf '')
ORANGE := $(shell tput setaf 208 2>/dev/null || printf '')
NC     := $(shell tput sgr0 2>/dev/null || printf '')
# fallback if tput not available (e.g. minimal Termux)
ifeq ($(ORANGE),)
    ORANGE := \033[38;5;208m
    NC     := \033[0m
    BOLD   := \033[1m
endif

APP    := $(ORANGE)$(BOLD)SOTA Vid-Dl v3.0.1$(NC)
BRAND  := $(ORANGE)$(BOLD)FJ™ Cyberzilla$(NC)
FOOTER := $(ORANGE)--- $(APP) | $(BRAND) ---$(NC)

.DEFAULT_GOAL := help
.PHONY: help install run diagnose lint format clean update test coverage build dev

# ----- targets -----
help: ## Show this help message
	@printf "\n$(ORANGE)  ____   ___  _____    __     ___  ____   ____  _     $(NC)\n"
	@printf "$(ORANGE) / ___| / _ \|_   _|   \ \   / (_)|  _ \ |  _ \| |    $(NC)\n"
	@printf "$(ORANGE) \___ \| | | | | |      \ \ / /| || | | || | | | |    $(NC)\n"
	@printf "$(ORANGE)  ___) | |_| | | |       \ V / | || |_| || |_| | |___ $(NC)\n"
	@printf "$(ORANGE) |____/ \___/  |_|        \_/  |_||____/ |____/|_____|$(NC)\n\n"
	@printf "$(ORANGE)----------------------------------------------------------------------------------$(NC)\n"
	@printf "$(BOLD)$(APP)$(NC) $(ORANGE)$(BOLD)by FJ™ Cyberzilla Systems MMXXVI$(NC)\n"
	@printf "$(ORANGE)----------------------------------------------------------------------------------$(NC)\n\n"
	@printf "$(ORANGE)Commands:$(NC)\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(ORANGE)%-12s$(NC) %s\n", $$1, $$2}'
	@printf "\n$(FOOTER)\n"

install: ## Install main dependencies (production)
	@printf "$(ORANGE)Installing dependencies...$(NC)\n"
	@uv sync --no-dev
	@uv pip install -e .
	@printf "$(ORANGE)✔ Production installation complete.$(NC)\n"

dev: ## Install with development extras
	@printf "$(ORANGE)Installing development dependencies...$(NC)\n"
	@uv sync
	@uv pip install -e .
	@printf "$(ORANGE)✔ Development installation complete.$(NC)\n"

update: ## Update dependencies (uv lock --upgrade)
	@printf "$(ORANGE)Updating locked dependencies...$(NC)\n"
	@uv lock --upgrade
	@uv sync
	@printf "$(ORANGE)✔ Dependencies updated.$(NC)\n"

run: ## Launch the application
	@printf "$(ORANGE)Launching SOTA...$(NC)\n"
	@uv run python main.py

diagnose: ## Run system compatibility check
	@printf "$(ORANGE)Diagnosing environment...$(NC)\n"
	@uv run python -c "import yt_dlp, rich, mutagen, pydantic, tenacity, psutil, requests; print('Python deps: OK')"
	@command -v ffmpeg >/dev/null 2>&1 && echo "ffmpeg: found" || echo "$(ORANGE)⚠ FFmpeg not found!$(NC)"
	@command -v aria2c >/dev/null 2>&1 && echo "aria2c: found" || echo "$(ORANGE)⚠ aria2c not found (optional)$(NC)"
	@printf "$(ORANGE)Diagnosis complete.$(NC)\n"

lint: ## Run ruff linter
	@uv run ruff check .

format: ## Run ruff formatter
	@uv run ruff format .

clean: ## Remove temporary files and caches
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
	@rm -rf build/ dist/ *.egg-info/ .ruff_cache/ .pytest_cache/ .mypy_cache/ htmlcov/
	@printf "$(ORANGE)✔ Project cleaned.$(NC)\n"

test: ## Run test suite with coverage
	@printf "$(ORANGE)Running tests...$(NC)\n"
	@PYTHONPATH=. uv run pytest --cov --cov-report=html --cov-report=term

coverage: ## Open coverage report (default browser)
	@printf "$(ORANGE)Opening coverage report...$(NC)\n"
	@xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || true

build: ## Build distributable package
	@printf "$(ORANGE)Building package...$(NC)\n"
	@uv build
	@printf "$(ORANGE)✔ Package built in dist/.$(NC)\n"
