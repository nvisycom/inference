# syntax=docker/dockerfile:1
# OCR inference service (PaddleOCR PP-OCRv5).
# Build context is the repo root (the uv workspace), so the shared nvisy-core
# package resolves:  docker build -f docker/ocr.Dockerfile -t inference-ocr .

ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Install deps first (cached) from the lockfile, then the project source.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=packages/nvisy-core/pyproject.toml,target=packages/nvisy-core/pyproject.toml \
    --mount=type=bind,source=packages/nvisy-ocr/pyproject.toml,target=packages/nvisy-ocr/pyproject.toml \
    uv sync --locked --package nvisy-ocr --no-install-workspace --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package nvisy-ocr --no-dev

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
# PaddleOCR/OpenCV need a couple of native libs at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Optional BYO weights mount point (see the root README docker-compose).
VOLUME ["/models"]
EXPOSE 8000
CMD ["bentoml", "serve", "nvisy_ocr.service:OcrService", "--host", "0.0.0.0", "--port", "8000"]
