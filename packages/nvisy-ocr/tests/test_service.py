"""Smoke tests for the OCR service scaffold."""

import bentoml
from nvisy_core.ocr import OcrRequest
from nvisy_ocr.service import OcrService


def test_request_model_validates():
    req = OcrRequest(image_b64="", confidence_threshold=0.5)
    assert req.confidence_threshold == 0.5


def test_service_exposes_recognize_endpoint():
    assert isinstance(OcrService, bentoml.Service)
    assert OcrService.name == "nvisy-inference-ocr"
    assert "recognize" in OcrService.apis
