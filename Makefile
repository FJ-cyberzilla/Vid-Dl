# SOTA Downloader Makefile (Orange theme)
# FJ™ Cyberzilla Systems

ORANGE := \033[38;5;208m
GREEN  := \033[32m
NC     := \033[0m

# Footer
FOOTER_MSG = $(ORANGE)-- SOTA Downloader · FJ™ Cybertronic$(NC)

.PHONY: help install diagnose clean lint format

help: ## Show this help message
	@printf "$(ORANGE)SOTA Commands:$(NC)\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(ORANGE)%-15s$(NC) %s\n", $$1, $$2}'
	@printf "\n"
	@printf "$(ORANGE)FJ™ Cyberzilla Systems — Professional Downloader$(NC)\n"
	@printf "\n"

install: ## Install dependencies and project in editable mode
	@printf "$(ORANGE)Installing SOTA Downloader...$(NC)\n"
	pip install -r requirements.txt
	pip install -e .
	@printf "$(GREEN)✔ Installation complete.$(NC)\n"
	@printf "$(FOOTER_MSG)\n"

diagnose: ## Run a system compatibility check
	@printf "$(ORANGE)Checking dependencies...$(NC)\n"
	@python3 -c "import yt_dlp, rich, mutagen; print('Dependencies: OK')"
	@which ffmpeg || echo "FFMPEG NOT FOUND: Run 'pkg install ffmpeg'"
	@printf "$(ORANGE)Checking Storage Access...$(NC)\n"
	@ls -ld /storage/emulated/0/DCIM/SOTADownloader || echo "Storage directory not yet created."
	@printf "$(GREEN)✔ Diagnosis complete.$(NC)\n"
	@printf "$(FOOTER_MSG)\n"

lint: ## Run pylint on the project
	pylint --rcfile=.pylintrc .
	@printf "$(FOOTER_MSG)\n"

format: ## Run black auto-formatter
	black .
	@printf "$(FOOTER_MSG)\n"

clean: ## Remove temporary cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/
	@printf "$(GREEN)✔ Cleaned project artifacts.$(NC)\n"
	@printf "$(FOOTER_MSG)\n"
