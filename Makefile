# ============================================================================
# Makefile for fiware_actuators_setup
# ============================================================================
# Usage: make <target>
# Run 'make help' to see all available targets
# ============================================================================

# Use PowerShell as the shell for Windows compatibility
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -Command

# Virtual environment paths
VENV := .venv/Scripts
PYTHON := $(VENV)/python.exe
PIP := $(VENV)/pip.exe
PYTEST := $(VENV)/pytest.exe
PYLINT := $(VENV)/pylint.exe
MYPY := $(VENV)/mypy.exe
ISORT := $(VENV)/isort.exe
BLACK := $(VENV)/black.exe
PRECOMMIT := $(VENV)/pre-commit.exe

.PHONY: help install install-dev test test-unit test-integration lint format \
        type-check docker-up docker-down docker-logs clean pre-commit all

# Default target
help:
	@Write-Host ""
	@Write-Host "========================================"
	@Write-Host "  fiware_actuators_setup - Makefile"
	@Write-Host "========================================"
	@Write-Host ""
	@Write-Host "Available targets:"
	@Write-Host ""
	@Write-Host "  Setup:"
	@Write-Host "    install        - Install production dependencies"
	@Write-Host "    install-dev    - Install all dependencies (dev included)"
	@Write-Host ""
	@Write-Host "  Testing:"
	@Write-Host "    test           - Run all tests"
	@Write-Host "    test-unit      - Run only unit tests (no integration)"
	@Write-Host "    test-integration - Run only integration tests"
	@Write-Host ""
	@Write-Host "  Code Quality:"
	@Write-Host "    lint           - Run pylint on source code"
	@Write-Host "    format         - Format code with isort and black"
	@Write-Host "    type-check     - Run mypy type checking"
	@Write-Host "    pre-commit     - Run all pre-commit hooks"
	@Write-Host ""
	@Write-Host "  Docker:"
	@Write-Host "    docker-up      - Start FIWARE services"
	@Write-Host "    docker-down    - Stop FIWARE services"
	@Write-Host "    docker-logs    - Show container logs"
	@Write-Host ""
	@Write-Host "  Utilities:"
	@Write-Host "    clean          - Remove cache and temp files"
	@Write-Host "    all            - Run format, lint, type-check, and test-unit"
	@Write-Host ""

# ============================================================================
# Setup
# ============================================================================

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	$(PRECOMMIT) install

# ============================================================================
# Testing
# ============================================================================

test:
	$(PYTEST) tests/ -v

test-unit:
	$(PYTEST) -m "not integration" -v

test-integration:
	$(PYTEST) -m integration -v

# ============================================================================
# Code Quality
# ============================================================================

lint:
	$(PYLINT) src/ --rcfile=.pylintrc

format:
	$(ISORT) src/ tests/
	$(BLACK) src/ tests/

type-check:
	$(MYPY) src/ --config-file=pyproject.toml

pre-commit:
	$(PRECOMMIT) run --all-files

# ============================================================================
# Docker
# ============================================================================

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# ============================================================================
# Utilities
# ============================================================================

clean:
	@if (Test-Path ".mypy_cache") { Remove-Item -Recurse -Force ".mypy_cache" }
	@if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
	@if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
	@if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
	@Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Run all quality checks and unit tests
all: format lint type-check test-unit
