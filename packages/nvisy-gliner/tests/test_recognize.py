"""Integration test for the NER recognize endpoint, with GLiNER faked.

Drives the real BentoML service via ``to_asgi()`` + Starlette's TestClient so we
exercise request validation, the kinds->labels->kinds mapping, and the
span -> Entity contract — without downloading torch or any weights. The model is
replaced by a fake returning GLiNER-shaped spans.
"""

from __future__ import annotations

import sys
import types

import pytest


class _FakeGLiNER:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

    def predict_entities(self, text, labels, threshold=0.5):
        # Echo back a span only for the "person" label, to prove the
        # kind<->label round trip and that unmapped labels are dropped.
        spans = []
        if "person" in labels:
            spans.append({"text": "Ada", "label": "person", "score": 0.95, "start": 0, "end": 3})
        # An unmapped model label that classify() should drop.
        spans.append({"text": "x", "label": "mystery", "score": 0.9, "start": 4, "end": 5})
        return spans


@pytest.fixture(scope="module")
def client():
    # Clear the global prometheus registry so this module's service registers
    # its default metrics cleanly even when another service ran first in the
    # same process ("Duplicated timeseries").
    _reset_prometheus_registry()

    gliner = types.ModuleType("gliner")
    gliner.GLiNER = _FakeGLiNER
    sys.modules["gliner"] = gliner

    from nvisy_gliner.service import NerService
    from starlette.testclient import TestClient

    with TestClient(NerService.to_asgi()) as c:
        yield c


def _reset_prometheus_registry() -> None:
    from prometheus_client import REGISTRY

    for collector in list(REGISTRY._collector_to_names):
        REGISTRY.unregister(collector)


def test_recognize_maps_kinds_round_trip(client):
    resp = client.post(
        "/recognize",
        json={"requests": [{"text": "Ada Lovelace", "kinds": ["person_name"], "threshold": 0.5}]},
    )
    assert resp.status_code == 200
    entities = resp.json()[0]["entities"]
    # "person" span maps back to person_name; the unmapped "mystery" is dropped.
    assert len(entities) == 1
    assert entities[0]["kind"] == "person_name"
    assert (entities[0]["start"], entities[0]["end"]) == (0, 3)


def test_unrequested_kinds_yield_no_entities(client):
    # email_address maps to label "email", which the fake never returns.
    resp = client.post(
        "/recognize",
        json={"requests": [{"text": "Ada", "kinds": ["email_address"], "threshold": 0.5}]},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["entities"] == []


def test_rejects_empty_kinds(client):
    # kinds has min_length=1; BentoML surfaces input validation errors as 400.
    resp = client.post(
        "/recognize",
        json={"requests": [{"text": "Ada", "kinds": [], "threshold": 0.5}]},
    )
    assert resp.status_code == 400
