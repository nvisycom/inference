"""Integration test for the OCR recognize endpoint, with PaddleOCR faked.

Drives the real BentoML service via ``to_asgi()`` + Starlette's TestClient so we
exercise request validation, the batchable list contract, and the
PaddleOCR-output -> Page/Block/Line/Word mapping — without downloading
paddlepaddle or any weights. The model is replaced by a fake that returns canned
``predict()`` output in PaddleOCR's array shape.
"""

from __future__ import annotations

import base64
import os
import sys
import types

import pytest


class _FakePaddleOCR:
    """Returns one canned result in PaddleOCR's parallel-array shape."""

    def __init__(self, *args, **kwargs):
        pass

    def predict(self, _image):
        return [
            {
                "rec_texts": ["Ada", "Lovelace"],
                "rec_scores": [0.99, 0.40],
                "rec_polys": [
                    [[0, 0], [30, 0], [30, 10], [0, 10]],
                    [[0, 12], [60, 12], [60, 22], [0, 22]],
                ],
                "rec_boxes": [[0, 0, 30, 10], [0, 12, 60, 22]],
            }
        ]


@pytest.fixture(scope="module")
def client():
    # BentoML registers default metrics on the global prometheus registry when a
    # service is instantiated; a second service in the same process collides
    # ("Duplicated timeseries"). Clear the registry so this module's service
    # registers cleanly regardless of test order.
    _reset_prometheus_registry()

    # resolve_model() needs NVISY_MODEL_NAME (served bentos inject it); the value
    # is irrelevant here since PaddleOCR is faked.
    os.environ["NVISY_MODEL_NAME"] = "fake-version"

    # Fake the heavy module imported inside OcrService.__init__.
    paddleocr = types.ModuleType("paddleocr")
    paddleocr.PaddleOCR = _FakePaddleOCR
    sys.modules["paddleocr"] = paddleocr

    from nvisy_paddle.service import OcrService
    from starlette.testclient import TestClient

    with TestClient(OcrService.to_asgi()) as c:
        yield c


def _reset_prometheus_registry() -> None:
    from prometheus_client import REGISTRY

    for collector in list(REGISTRY._collector_to_names):
        REGISTRY.unregister(collector)


def _png_b64() -> str:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 24), "white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_recognize_maps_words_and_filters_by_confidence(client):
    resp = client.post(
        "/recognize",
        json={"requests": [{"image": _png_b64(), "confidenceThreshold": 0.5}]},
    )
    assert resp.status_code == 200
    page = resp.json()[0]["pages"][0]
    # Response serializes camelCase, matching the OpenAPI schema (regression
    # guard: this field was emitted as snake_case page_number before).
    assert "pageNumber" in page and "page_number" not in page
    words = page["blocks"][0]["lines"][0]["words"]
    # "Lovelace" (0.40) is below the 0.5 threshold and dropped; "Ada" stays.
    assert [w["text"] for w in words] == ["Ada"]
    assert words[0]["bbox"] == {"x": 0, "y": 0, "width": 30, "height": 10}
    assert words[0]["polygon"] is not None


def test_rejects_invalid_base64(client):
    resp = client.post(
        "/recognize",
        json={"requests": [{"image": "not!base64", "confidenceThreshold": 0.0}]},
    )
    assert resp.status_code == 400
