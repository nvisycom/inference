"""OCR wire contract, version 1.

Request carries a base64-encoded image; response is a ``Page -> Block -> Line ->
Word`` hierarchy. Geometry is reported as an axis-aligned bounding box plus an
optional 4-point polygon (engines that produce rotated regions, like PaddleOCR,
populate the polygon; others may omit it).

The Rust runtime (``nvisy-inference-client``) is the source of truth; these
models mirror it. The wire is camelCase to match the runtime's serde
``rename_all = "camelCase"``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# [x, y] image-space point. Origin top-left, pixels.
Point = tuple[float, float]


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BoundingBox(_Model):
    """Axis-aligned box in image pixels, origin top-left."""

    x: float
    y: float
    width: float
    height: float


class Word(_Model):
    text: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    bbox: BoundingBox
    # 4-point polygon [top-left, top-right, bottom-right, bottom-left]. Present
    # when the engine reports rotated/quadrilateral regions.
    polygon: list[Point] | None = None


class Line(_Model):
    text: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    bbox: BoundingBox
    polygon: list[Point] | None = None
    words: list[Word] = Field(default_factory=list)


class Block(_Model):
    text: str
    bbox: BoundingBox
    lines: list[Line] = Field(default_factory=list)


class Page(_Model):
    page_number: int = Field(ge=1, description="1-based page index.")
    width: float | None = Field(default=None, description="Page width in pixels.")
    height: float | None = Field(default=None, description="Page height in pixels.")
    blocks: list[Block] = Field(default_factory=list)


class OcrRequest(_Model):
    image: str = Field(description="Base64-encoded image bytes (PNG/JPEG/TIFF/WebP).")
    confidence_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Drop words below this recognition confidence.",
    )


class OcrResponse(_Model):
    pages: list[Page] = Field(default_factory=list)
