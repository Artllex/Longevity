package ?= longevity
POETRY ?= poetry

.DEFAULT_GOAL := help

# -----------------------
# Helpers
# -----------------------

.PHONY: help
help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: _check_git
_check_git:
	@command -v git >/dev/null 2>&1 || (echo "git is required. Install it: sudo apt install -y git" && exit 1)
	@git rev-parse --is-inside-work-tree >/dev/null 2>&1 || (echo "Not a git repository. Run: git init" && exit 1)

.PHONY: new
new: ## Create a new project from this template (runs scripts/project_creator.py)
	python3 scripts/project_creator.py

# -----------------------
# Environment
# -----------------------

# Resolve python path from pyenv (uses .python-version if present)
PYENV_PYTHON := $(shell pyenv which python 2>/dev/null)

.PHONY: python
python: ## Show active Python (pyenv + Poetry)
	@echo "pyenv python:  $(PYENV_PYTHON)"
	@python --version || true
	@$(POETRY) run python --version 2>/dev/null || true

# .python-version is the single source of truth
PYTHON_VERSION_FILE := .python-version
PYENV_VERSION := $(strip $(shell test -f $(PYTHON_VERSION_FILE) && cat $(PYTHON_VERSION_FILE)))
PYENV_PYTHON := $(shell pyenv prefix $(PYENV_VERSION) 2>/dev/null)/bin/python

.PHONY: _check_pyenv
_check_pyenv:
	@command -v pyenv >/dev/null 2>&1 || (echo "pyenv is required but not found in PATH. Install pyenv and restart your shell."; exit 1)
	@test -f "$(PYTHON_VERSION_FILE)" || (echo "Missing $(PYTHON_VERSION_FILE). Create it with e.g.: echo '3.11.14' > $(PYTHON_VERSION_FILE)"; exit 1)
	@test -n "$(PYENV_VERSION)" || (echo "$(PYTHON_VERSION_FILE) is empty. Put a version there, e.g. 3.11.14"; exit 1)

.PHONY: _ensure_pyenv_python
_ensure_pyenv_python: _check_pyenv
	@echo "🔎 Required Python (pyenv): $(PYENV_VERSION)"
	@if ! pyenv versions --bare | grep -Fxq "$(PYENV_VERSION)"; then \
		echo "⬇️  Python $(PYENV_VERSION) not installed in pyenv. Installing..."; \
		pyenv install "$(PYENV_VERSION)"; \
	else \
		echo "✅ Python $(PYENV_VERSION) already installed in pyenv."; \
	fi
	@pyenv local "$(PYENV_VERSION)" >/dev/null
	@echo "📌 pyenv local set to: $$(pyenv local)"

.PHONY: env
env: _ensure_pyenv_python ## Create/attach Poetry venv using pyenv python, then install deps
	@PYENV_PYTHON="$$(pyenv prefix "$(PYENV_VERSION)")/bin/python"; \
	if [ ! -x "$$PYENV_PYTHON" ]; then \
		echo "❌ Could not resolve interpreter path: $$PYENV_PYTHON"; \
		echo "Try: pyenv prefix $(PYENV_VERSION)"; \
		exit 1; \
	fi; \
	echo "🐍 Using pyenv interpreter: $$PYENV_PYTHON"; \
	$(POETRY) env use "$$PYENV_PYTHON"; \
	$(POETRY) install

.PHONY: install
install: ## Install dependencies (Poetry venv)
	$(POETRY) install

.PHONY: update
update: ## Refresh lock + install
	$(POETRY) lock
	$(POETRY) install

.PHONY: shell
shell: ## Print command to activate Poetry venv (Poetry 2.x)
	@$(POETRY) env activate

# -----------------------
# Run / Quality
# -----------------------

.PHONY: run
run: ## Run the app
	$(POETRY) run python -m $(package).main

.PHONY: format
format: ## Format code (ruff)
	$(POETRY) run ruff format .

.PHONY: lint
lint: ## Lint code (ruff)
	$(POETRY) run ruff check .

.PHONY: fix
fix: ## Auto-fix lint issues (safe) + format
	$(POETRY) run ruff check . --fix
	$(POETRY) run ruff format .

.PHONY: typecheck
typecheck: ## Type-check (mypy)
	$(POETRY) run mypy .

.PHONY: test
test: ## Run tests
	$(POETRY) run pytest

.PHONY: cov
cov: ## Tests + coverage
	$(POETRY) run pytest --cov=$(package) --cov-report=term-missing

# -----------------------
# Composite
# -----------------------

.PHONY: check
check: format lint typecheck test ## Format + lint + typecheck + tests

.PHONY: ci
ci: lint typecheck test ## CI entrypoint (no auto-formatting)
	@true

# -----------------------
# Pre-commit
# -----------------------

.PHONY: setup
setup: _check_git install ## Install deps + git hooks, then run hooks once
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit run --all-files

.PHONY: precommit
precommit: _check_git ## Run pre-commit on all files
	$(POETRY) run pre-commit run --all-files

.PHONY: precommit-update
precommit-update: ## Update pre-commit hooks (MODIFIES repo)
	$(POETRY) run pre-commit autoupdate
	$(POETRY) run pre-commit run --all-files

# -----------------------
# Clean
# -----------------------

CLEAN_DIRS := \
	__pycache__ \
	.pytest_cache \
	.ruff_cache \
	.mypy_cache \
	dist \
	build \
	*.egg-info

.PHONY: clean
clean: ## Remove caches and build artifacts
	@for d in $(CLEAN_DIRS); do \
		find . -type d -name "$$d" -prune -exec rm -rf {} +; \
	done
