"""OCR inference service (PaddleOCR PP-OCRv5) exposed over HTTP via BentoML.

The default implementation of the OCR wire contract (``nvisy_core.ocr.v1``).

Run locally::

    uv run bentoml serve nvisy_paddle.service:OcrService --reload
"""

from __future__ import annotations

import base64
import binascii
import io
import os
import os.path
from typing import TYPE_CHECKING

import bentoml
from bentoml.exceptions import InvalidArgument, ServiceUnavailable
from nvisy_core.ocr.v1 import Block, BoundingBox, Line, OcrRequest, OcrResponse, Page, Word
from nvisy_core.runtime import get_logger, request_id, resolve_model
from prometheus_client import Histogram

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

logger = get_logger("nvisy.paddle")

# Default OCR version (NVISY_MODEL_NAME overrides; NVISY_MODEL_PATH / /models
# mount overrides with on-disk weights). See nvisy_core.runtime.resolve_model.
DEFAULT_MODEL = "PP-OCRv5"

# Effective batch size, to see whether adaptive batching actually fills.
# prometheus_client directly (bentoml.metrics is deprecated in 1.4); BentoML
# sets PROMETHEUS_MULTIPROC_DIR so this is multiprocess-safe across workers.
batch_size_metric = Histogram(
    "nvisy_ocr_batch_size",
    "Number of images merged into one recognize() call.",
    buckets=(1, 2, 4, 8, 16),
)

# BentoML builds the image from this config (`bentoml build` + `containerize`);
# no hand-written Dockerfile. The requirements file is exported per-service from
# the workspace lock (scripts/gen_requirements.py) so the image installs only
# this service's resolved deps, including the editable nvisy-core. What source
# gets bundled is scoped by bentofile.yaml's `include`. PaddleOCR/OpenCV need
# libgl1. lock_python_packages=False: the file is already locked + hashed, so
# BentoML must not re-resolve it.
image = (
    bentoml.images.Image(python_version="3.12", lock_python_packages=False)
    .system_packages("libgl1", "libglib2.0-0")
    .requirements_file("packages/nvisy-paddle/requirements.txt")
)


@bentoml.service(
    name="nvisy-inference-paddle",
    image=image,
    resources={"cpu": "2"},
    # ADR default; profile and tune later.
    traffic={"timeout": 60},
    envs=[
        {"name": "NVISY_MODEL_PATH"},
        {"name": "NVISY_MODEL_NAME"},
        {"name": "NVISY_OCR_LANG"},
        {"name": "LOG_LEVEL"},
    ],
)
class OcrService:
    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        model = resolve_model(DEFAULT_MODEL)
        # PP-OCRv5 is multilingual (106 languages). lang selects the recognition
        # model at init (one per process); unset uses PaddleOCR's default model,
        # which covers Simplified/Traditional Chinese, Pinyin, English and
        # Japanese. NVISY_OCR_LANG picks a specific language model (e.g.
        # "korean", "fr", "cyrillic").
        lang = os.getenv("NVISY_OCR_LANG")
        logger.info("loading PaddleOCR (model=%s, lang=%s)", model, lang or "<default>")
        # Detection + recognition only — no doc orientation / unwarping (the
        # runtime handles page geometry upstream). A resolved value that is an
        # existing directory is a mounted/BYO weights dir; otherwise it's an OCR
        # version like "PP-OCRv5".
        common: dict = {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
        }
        if lang:
            common["lang"] = lang
        if os.path.isdir(model):
            self.ocr = PaddleOCR(
                text_detection_model_dir=model,
                text_recognition_model_dir=model,
                **common,
            )
        else:
            self.ocr = PaddleOCR(ocr_version=model, **common)
        logger.info("PaddleOCR ready")

    @bentoml.api(batchable=True, max_batch_size=8, max_latency_ms=120)
    async def recognize(
        self,
        requests: list[OcrRequest],
        ctx: bentoml.Context,
    ) -> list[OcrResponse]:
        if self.ocr is None:  # pragma: no cover - defensive; __init__ loads eagerly
            raise ServiceUnavailable("OCR model is not loaded")
        batch_size_metric.observe(len(requests))
        logger.info("recognize batch=%d req_id=%s", len(requests), request_id(ctx))
        return [self._recognize_one(req) for req in requests]

    def _recognize_one(self, req: OcrRequest) -> OcrResponse:
        image = _decode_image(req.image)
        # predict() returns one result per input image; we pass one.
        results = self.ocr.predict(_to_ndarray(image))
        page = _result_to_page(results[0] if results else None, image, req.confidence_threshold)
        return OcrResponse(pages=[page])


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


def _result_to_page(result, image: PILImage, threshold: float) -> Page:
    """Map one PaddleOCR result into a single-block, single-line Page.

    PaddleOCR returns parallel arrays: ``rec_texts`` (strings), ``rec_scores``
    (floats), ``rec_polys`` (4-point quads) and ``rec_boxes`` (axis-aligned
    [x1, y1, x2, y2]). Each recognized text becomes a Word; we group them all
    under one Line/Block, mirroring how the runtime's PaddleX backend flattens
    word-level output.
    """
    width, height = image.size
    words: list[Word] = []
    if result is not None:
        texts = result.get("rec_texts", [])
        scores = result.get("rec_scores", [])
        polys = result.get("rec_polys", [])
        boxes = result.get("rec_boxes", [])
        for i, text in enumerate(texts):
            score = float(scores[i]) if i < len(scores) else None
            if score is not None and score < threshold:
                continue
            words.append(
                Word(
                    text=text,
                    confidence=score,
                    bbox=_box_to_bbox(boxes[i]) if i < len(boxes) else _BBOX_ZERO,
                    polygon=_poly_to_points(polys[i]) if i < len(polys) else None,
                )
            )
    full_text = " ".join(w.text for w in words)
    bbox = _BBOX_ZERO if not words else BoundingBox(x=0, y=0, width=width, height=height)
    line = Line(text=full_text, bbox=bbox, words=words)
    block = Block(text=full_text, bbox=bbox, lines=[line] if words else [])
    return Page(page_number=1, width=width, height=height, blocks=[block] if words else [])


_BBOX_ZERO = BoundingBox(x=0, y=0, width=0, height=0)


def _box_to_bbox(box) -> BoundingBox:
    x1, y1, x2, y2 = (float(v) for v in box)
    return BoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def _poly_to_points(poly) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in poly]
