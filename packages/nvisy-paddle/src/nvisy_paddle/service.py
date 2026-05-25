"""OCR inference service (PaddleOCR PP-OCRv5) exposed over HTTP via BentoML.

The default implementation of the OCR wire contract (``nvisy_core.ocr.v1``).
Scaffold stub — PaddleOCR wiring is filled in by a follow-up.

Run locally::

    uv run bentoml serve nvisy_paddle.service:OcrService --reload
"""

from __future__ import annotations

import bentoml
from nvisy_core.ocr.v1 import OcrRequest, OcrResponse


@bentoml.service(
    name="nvisy-inference-paddle",
    resources={"cpu": "2"},
    # ADR default; profile and tune later.
    traffic={"timeout": 60},
)
class OcrService:
    def __init__(self) -> None:
        # TODO(follow-up): load PaddleOCR PP-OCRv5 here.
        #   from paddleocr import PaddleOCR
        #   self.ocr = PaddleOCR(lang="en", ocr_version="PP-OCRv5",
        #                        use_doc_orientation_classify=False,
        #                        use_doc_unwarping=False)
        self.ocr = None

    @bentoml.api(batchable=True, max_batch_size=8, max_latency_ms=120)
    async def recognize(self, requests: list[OcrRequest]) -> list[OcrResponse]:
        raise NotImplementedError("OCR inference not wired yet (scaffold stub).")
