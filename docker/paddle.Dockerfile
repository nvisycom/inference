# syntax=docker/dockerfile:1
# OCR inference service (PaddleOCR PP-OCRv5) — default OCR implementation.
# Build context is the repo root (the uv workspace), so the shared nvisy-core
# package resolves:  docker build -f docker/paddle.Dockerfile -t inference-paddle .

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
    --mount=type=bind,source=packages/nvisy-paddle/pyproject.toml,target=packages/nvisy-paddle/pyproject.toml \
    uv sync --locked --package nvisy-paddle --no-install-workspace --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package nvisy-paddle --no-dev

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
CMD ["bentoml", "serve", "nvisy_paddle.service:OcrService", "--host", "0.0.0.0", "--port", "8000"]
