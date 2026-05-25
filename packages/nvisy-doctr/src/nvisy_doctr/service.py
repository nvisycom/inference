"""OCR inference service (docTR) exposed over HTTP via BentoML.

The default implementation of the OCR wire contract (``nvisy_core.ocr.v1``).
docTR natively produces a ``Document -> Page -> Block -> Line -> Word`` hierarchy
with word-level geometry, which maps directly onto our contract.

Run locally::

    uv run bentoml serve nvisy_doctr.service:OcrService --reload
"""

from __future__ import annotations

import base64
import binascii
import io
from typing import TYPE_CHECKING

import bentoml
from bentoml.exceptions import BentoMLException, InternalServerError, InvalidArgument
from nvisy_core.ocr.v1 import (
    Block,
    BlockKind,
    BoundingBox,
    Line,
    OcrRequest,
    OcrResponse,
    Page,
    Word,
)
from nvisy_core.runtime import get_logger, request_id, resolve_model
from prometheus_client import Histogram

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = get_logger("nvisy.doctr")

# Built-in default detection + recognition models, joined as "det+rec".
# Declared as the NVISY_MODEL_NAME env default below (single source of truth).
DEFAULT_MODEL = "db_resnet50+crnn_vgg16_bn"

batch_size_metric = Histogram(
    "nvisy_ocr_batch_size",
    "Number of images merged into one recognize() call.",
    buckets=(1, 2, 4, 8, 16),
)

# BentoML builds the image from this config (`bentoml build` + `containerize`);
# no hand-written Dockerfile. The requirements file is exported per-service from
# the workspace lock (scripts/gen_requirements.py); bundled source is scoped by
# bentofile.yaml's `include`. docTR/OpenCV need libgl1. lock_python_packages=
# False: the file is already locked + hashed, so BentoML must not re-resolve it.
image = (
    bentoml.images.Image(python_version="3.12", lock_python_packages=False)
    .system_packages("libgl1", "libglib2.0-0")
    .requirements_file("packages/nvisy-doctr/requirements.txt")
)


@bentoml.service(
    name="nvisy-inference-doctr",
    image=image,
    resources={"cpu": "2"},
    traffic={"timeout": 60},
    # Declared with defaults so they're optional + documented in the bento
    # manifest. NVISY_MODEL_PATH defaults to the /models mount (empty unless BYO
    # weights are mounted); NVISY_MODEL_NAME is the "det+rec" pair otherwise.
    envs=[
        {"name": "NVISY_MODEL_PATH", "value": "/models"},
        {"name": "NVISY_MODEL_NAME", "value": DEFAULT_MODEL},
    ],
)
class OcrService:
    def __init__(self) -> None:
        from doctr.models import ocr_predictor

        self.model_id = resolve_model()
        det, _, rec = self.model_id.partition("+")
        if not rec:
            raise RuntimeError(f"NVISY_MODEL_NAME must be 'det+rec', got {self.model_id!r}")
        logger.info("loading docTR (det=%s, rec=%s)", det, rec)
        self.ocr = ocr_predictor(det, rec, pretrained=True)
        logger.info("docTR ready")

    # Sync (not async): inference is CPU/GPU-bound and blocking. BentoML runs
    # sync endpoints in a managed thread pool, so this never blocks the event
    # loop (an async def here would, and could starve /readyz).
    @bentoml.api(batchable=True, max_batch_size=8, max_latency_ms=120)
    def recognize(
        self,
        requests: list[OcrRequest],
        ctx: bentoml.Context,
    ) -> list[OcrResponse]:
        batch_size_metric.observe(len(requests))
        rid = request_id(ctx)
        logger.info("recognize batch=%d req_id=%s", len(requests), rid)
        try:
            return [self._recognize_one(req) for req in requests]
        except BentoMLException:
            # Typed request errors (e.g. InvalidArgument for bad image bytes)
            # carry their own status; let them through unchanged.
            raise
        except Exception as exc:
            logger.exception("inference failed (req_id=%s)", rid)
            raise InternalServerError("OCR inference failed") from exc

    def _recognize_one(self, req: OcrRequest) -> OcrResponse:
        image = _decode_image(req.image)
        result = self.ocr([_to_ndarray(image)])
        page = _page_from_doctr(result.pages[0], req.confidence_threshold)
        return OcrResponse(pages=[page], model_id=self.model_id)


def _decode_image(image_b64: str) -> PILImage:
    from PIL import Image, UnidentifiedImageError

    try:
        raw = base64.b64decode(image_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InvalidArgument("image is not valid base64") from exc
    try:
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise InvalidArgument("image bytes are not a recognizable image") from exc


def _to_ndarray(image: PILImage):
    import numpy as np

    return np.asarray(image)


def _page_from_doctr(page, threshold: float) -> Page:
    """Map a docTR page onto the contract.

    docTR geometry is normalized [0, 1] relative to the page; ``dimensions`` is
    ``(height, width)`` in pixels. We scale geometry to pixels and keep the full
    Block -> Line -> Word hierarchy docTR produces. Base docTR has no layout
    classification, so blocks default to BlockKind.TEXT.
    """
    height, width = page.dimensions

    blocks: list[Block] = []
    for db in page.blocks:
        lines: list[Line] = []
        for dl in db.lines:
            words = [
                Word(
                    text=dw.value,
                    confidence=float(dw.confidence),
                    bbox=_geom_to_bbox(dw.geometry, width, height),
                )
                for dw in dl.words
                if dw.confidence >= threshold
            ]
            if not words:
                continue
            lines.append(
                Line(
                    text=" ".join(w.text for w in words),
                    bbox=_geom_to_bbox(dl.geometry, width, height),
                    words=words,
                )
            )
        if not lines:
            continue
        block_text = "\n".join(line.text for line in lines)
        blocks.append(
            Block(
                text=block_text,
                kind=BlockKind.TEXT,
                bbox=_geom_to_bbox(db.geometry, width, height),
                lines=lines,
            )
        )

    return Page(page_number=1, width=float(width), height=float(height), blocks=blocks)


def _geom_to_bbox(geometry, width: int, height: int) -> BoundingBox:
    """Convert docTR normalized ((xmin,ymin),(xmax,ymax)) to a pixel BoundingBox."""
    (xmin, ymin), (xmax, ymax) = geometry
    return BoundingBox(
        x=xmin * width,
        y=ymin * height,
        width=(xmax - xmin) * width,
        height=(ymax - ymin) * height,
    )
