"""Smoke tests for the OCR service scaffold."""

import bentoml
from nvisy_core.ocr.v1 import BoundingBox, OcrRequest, OcrResponse, Page, Word
from nvisy_paddle.service import OcrService


def test_request_model_validates():
    req = OcrRequest(image="", confidence_threshold=0.5)
    assert req.confidence_threshold == 0.5


def test_response_round_trips_camel_case():
    page = Page(
        page_number=1,
        blocks=[],
    )
    resp = OcrResponse(pages=[page])
    dumped = resp.model_dump(by_alias=True)
    assert dumped["pages"][0]["pageNumber"] == 1


def test_word_geometry_has_bbox_and_optional_polygon():
    word = Word(text="hi", bbox=BoundingBox(x=0, y=0, width=10, height=4))
    assert word.polygon is None
    assert word.bbox.width == 10


def test_service_exposes_recognize_endpoint():
    assert isinstance(OcrService, bentoml.Service)
    assert OcrService.name == "nvisy-inference-paddle"
    assert "recognize" in OcrService.apis
