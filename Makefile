# Makefile for the Nvisy inference monorepo (uv workspace + BentoML services).

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default to a single recipe shell so a failure inside a piped
# command (e.g. server panics under `tee`) is reported by make.
.SHELLFLAGS := -eu -o pipefail -c
SHELL       := /bin/bash

# Services and their published image names, keyed by package suffix.
SERVICES := paddle gliner

.PHONY: bento
bento:  ## Install BentoML and all workspace dependencies into the venv.
	@uv sync --all-packages

.PHONY: lint
lint:  ## Run ruff check + format check.
	@uv run ruff check .
	@uv run ruff format --check .

.PHONY: fmt
fmt:  ## Auto-format with ruff.
	@uv run ruff format .
	@uv run ruff check --fix .

.PHONY: test
test:  ## Run the test suite.
	@uv run pytest

.PHONY: generate
generate:  ## Regenerate OpenAPI specs and per-service requirements.
	@uv run python scripts/gen_openapi.py
	@uv run python scripts/gen_requirements.py

.PHONY: check
check:  ## Fail if generated OpenAPI specs / requirements are stale (CI parity).
	@uv run python scripts/gen_openapi.py --check
	@uv run python scripts/gen_requirements.py --check

.PHONY: serve-paddle
serve-paddle:  ## Serve the OCR (PaddleOCR) service locally with reload.
	@uv run bentoml serve nvisy_paddle.service:OcrService --reload

.PHONY: serve-gliner
serve-gliner:  ## Serve the NER (GLiNER) service locally with reload.
	@uv run bentoml serve nvisy_gliner.service:NerService --reload

.PHONY: build
build:  ## Build both Bentos from their bentofiles.
	@for s in $(SERVICES); do \
		uv run bentoml build -f packages/nvisy-$$s/bentofile.yaml . ; \
	done

.PHONY: containerize
containerize:  ## Build + containerize both Bentos into local Docker images.
	@for s in $(SERVICES); do \
		uv run bentoml build -f packages/nvisy-$$s/bentofile.yaml --containerize . ; \
	done

.PHONY: ci
ci: lint check test  ## Run all CI checks locally.

# `help` parses the `## …` doc comment after each target name and
# prints `target — description`. Keeping help auto-generated from
# the targets themselves means new targets don't need a manual
# entry to show up.
.PHONY: help
help:  ## Show this help.
	@awk 'BEGIN { FS = ":.*## " } /^[a-zA-Z0-9_.-]+:.*## / { printf "  %-14s  %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
