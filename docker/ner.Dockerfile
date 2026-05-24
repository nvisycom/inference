# syntax=docker/dockerfile:1
# NER inference service (GLiNER).
# Build context is the repo root (the uv workspace), so the shared nvisy-core
# package resolves:  docker build -f docker/ner.Dockerfile -t inference-ner .

ARG PYTHON_VERSION=3.12

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=packages/nvisy-core/pyproject.toml,target=packages/nvisy-core/pyproject.toml \
    --mount=type=bind,source=packages/nvisy-ner/pyproject.toml,target=packages/nvisy-ner/pyproject.toml \
    uv sync --locked --package nvisy-ner --no-install-workspace --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package nvisy-ner --no-dev

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Optional BYO weights mount point (see the root README docker-compose).
VOLUME ["/models"]
EXPOSE 8000
CMD ["bentoml", "serve", "nvisy_ner.service:NerService", "--host", "0.0.0.0", "--port", "8000"]
