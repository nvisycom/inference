"""Shared runtime helpers for the inference services.

Kept dependency-light (no BentoML import) so ``nvisy-core`` stays a pure
contract + utilities package: model-path resolution for bring-your-own-weights,
and a logger that stamps every line with the request's correlation id.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Where mounted/BYO weights are expected (see the README docker-compose).
DEFAULT_MODEL_DIR = "/models"
# Env var a deployment sets to point at custom weights.
MODEL_PATH_ENV = "NVISY_MODEL_PATH"
# Header the Rust runtime sends to correlate a request across services.
REQUEST_ID_HEADER = "x-request-id"


def resolve_model_path(default_model: str) -> str:
    """Resolve the model to load for bring-your-own-weights.

    Returns ``$NVISY_MODEL_PATH`` if set, else ``/models`` when it exists and is
    non-empty (mounted weights), else ``default_model`` — a model id the runtime
    downloads (e.g. a Hugging Face repo) for the zero-config case.
    """
    explicit = os.getenv(MODEL_PATH_ENV)
    if explicit:
        return explicit
    mounted = Path(DEFAULT_MODEL_DIR)
    if mounted.is_dir() and any(mounted.iterdir()):
        return str(mounted)
    return default_model


def get_logger(name: str) -> logging.Logger:
    """A logger for a service; honors the LOG_LEVEL env var (default INFO)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    return logger


def request_id(ctx: object) -> str:
    """Pull the correlation id from a BentoML request context, or ``"-"``.

    BentoML exposes request headers on ``ctx.request.headers``. We read the
    runtime-supplied ``x-request-id`` so service logs can be correlated with the
    caller; absent it, returns ``"-"`` rather than raising.
    """
    headers = getattr(getattr(ctx, "request", None), "headers", None)
    if headers is None:
        return "-"
    try:
        return headers.get(REQUEST_ID_HEADER, "-")
    except (AttributeError, TypeError):
        return "-"
