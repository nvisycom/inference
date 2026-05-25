# Makefile for the Nvisy inference monorepo (uv workspace + BentoML services).

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default to a single recipe shell so a failure inside a piped
# command (e.g. server panics under `tee`) is reported by make.
.SHELLFLAGS := -eu -o pipefail -c
SHELL       := /bin/bash

# Timestamped log line, tagged with the running target. Use as `$(call log,msg)`.
define log
printf "[%s] [MAKE] [$(MAKECMDGOALS)] $(1)\n" "$$(date '+%Y-%m-%d %H:%M:%S')"
endef

# Services, keyed by package suffix (packages/nvisy-<suffix>).
SERVICES := doctr gliner

.PHONY: bento
bento:  ## Install BentoML and all workspace dependencies into the venv.
	@$(call log,Syncing workspace...)
	@uv sync --all-packages
	@$(call log,Workspace ready.)

.PHONY: lint
lint:  ## Run ruff check + format check.
	@$(call log,Running ruff check...)
	@uv run ruff check .
	@$(call log,Running format check...)
	@uv run ruff format --check .
	@$(call log,Lint passed.)

.PHONY: fmt
fmt:  ## Auto-format with ruff.
	@$(call log,Formatting...)
	@uv run ruff format .
	@uv run ruff check --fix .
	@$(call log,Formatted.)

.PHONY: test
test:  ## Run the test suite.
	@$(call log,Running tests...)
	@uv run pytest

.PHONY: generate
generate:  ## Regenerate OpenAPI specs and per-service requirements.
	@$(call log,Regenerating OpenAPI specs...)
	@uv run python scripts/gen_openapi.py
	@$(call log,Regenerating service requirements...)
	@uv run python scripts/gen_requirements.py
	@$(call log,Generated.)

.PHONY: check
check:  ## Fail if generated OpenAPI specs / requirements are stale (CI parity).
	@$(call log,Checking OpenAPI specs...)
	@uv run python scripts/gen_openapi.py --check
	@$(call log,Checking service requirements...)
	@uv run python scripts/gen_requirements.py --check
	@$(call log,Generated artifacts up to date.)

.PHONY: serve-doctr
serve-doctr:  ## Serve the OCR (docTR) service locally with reload.
	@$(call log,Serving nvisy-doctr...)
	@uv run bentoml serve nvisy_doctr.service:OcrService --reload

.PHONY: serve-gliner
serve-gliner:  ## Serve the NER (GLiNER) service locally with reload.
	@$(call log,Serving nvisy-gliner...)
	@uv run bentoml serve nvisy_gliner.service:NerService --reload

.PHONY: build
build:  ## Build both Bentos from their bentofiles.
	@for s in $(SERVICES); do \
		$(call log,Building nvisy-$$s...); \
		uv run bentoml build -f packages/nvisy-$$s/bentofile.yaml . ; \
	done
	@$(call log,Bentos built.)

.PHONY: containerize
containerize:  ## Build + containerize both Bentos into local Docker images.
	@for s in $(SERVICES); do \
		$(call log,Containerizing nvisy-$$s...); \
		uv run bentoml build -f packages/nvisy-$$s/bentofile.yaml --containerize . ; \
	done
	@$(call log,Images built.)

.PHONY: ci
ci: lint check test  ## Run all CI checks locally.
	@$(call log,All CI checks passed!)

# `help` parses the `## …` doc comment after each target name and
# prints `target — description`. Keeping help auto-generated from
# the targets themselves means new targets don't need a manual
# entry to show up.
.PHONY: help
help:  ## Show this help.
	@awk 'BEGIN { FS = ":.*## " } /^[a-zA-Z0-9_.-]+:.*## / { printf "  %-14s  %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
