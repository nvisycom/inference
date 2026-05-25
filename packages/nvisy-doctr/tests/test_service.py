"""Smoke tests for the docTR OCR service."""

import bentoml
from nvisy_doctr.service import OcrService


def test_service_exposes_recognize_endpoint():
    assert isinstance(OcrService, bentoml.Service)
    assert OcrService.name == "nvisy-inference-doctr"
    assert "recognize" in OcrService.apis
