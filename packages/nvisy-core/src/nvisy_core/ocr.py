"""OCR wire contract: ``Page -> Block -> Line -> Word``.

Scaffold stub — finalized in the contract-design follow-up and kept in sync
with the Rust source of truth (``nvisy-inference-client``).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Model(BaseModel):
    # Wire is camelCase (matches the runtime's serde `rename_all = "camelCase"`).
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class OcrRequest(_Model):
    image_b64: str = Field(description="Base64-encoded image bytes (PNG/JPEG/...).")
    confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class Word(_Model):
    text: str
    confidence: float | None = None
    # 4-point polygon [[x, y], ...].
    polygon: list[tuple[float, float]] = Field(default_factory=list)


class Line(_Model):
    text: str
    words: list[Word] = Field(default_factory=list)


class Block(_Model):
    lines: list[Line] = Field(default_factory=list)


class Page(_Model):
    page_number: int
    width: float | None = None
    height: float | None = None
    blocks: list[Block] = Field(default_factory=list)


class OcrResponse(_Model):
    pages: list[Page] = Field(default_factory=list)
