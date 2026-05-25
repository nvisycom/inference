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
# Filesystem path to pre-fetched/mounted weights. Takes precedence over the name.
MODEL_PATH_ENV = "NVISY_MODEL_PATH"
# Model identifier to load/download (e.g. a Hugging Face repo id, or a
# framework-specific name like an OCR version) when no path is given.
MODEL_NAME_ENV = "NVISY_MODEL_NAME"
# Header the Rust runtime sends to correlate a request across services.
REQUEST_ID_HEADER = "x-request-id"


def resolve_model(default_name: str) -> str:
    """Resolve which model a service should load (bring-your-own-weights).

    Precedence:

    1. ``$NVISY_MODEL_PATH`` — a filesystem path to weights, if set.
    2. ``/models`` — when mounted and non-empty (the conventional BYO mount).
    3. ``$NVISY_MODEL_NAME`` — a model identifier to load/download.
    4. ``default_name`` — the service's built-in default identifier.

    Returns either a local path (cases 1-2) or a model identifier (cases 3-4);
    both PaddleOCR and ``GLiNER.from_pretrained`` accept either form.
    """
    path = os.getenv(MODEL_PATH_ENV)
    if path:
        return path
    mounted = Path(DEFAULT_MODEL_DIR)
    if mounted.is_dir() and any(mounted.iterdir()):
        return str(mounted)
    return os.getenv(MODEL_NAME_ENV) or default_name


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
