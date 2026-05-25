"""Integration test for the NER recognize endpoint, with GLiNER faked.

Drives the real BentoML service via ``to_asgi()`` + Starlette's TestClient so we
exercise request validation, the kinds->labels->kinds mapping, and the
span -> Entity contract — without downloading torch or any weights. The model is
replaced by a fake returning GLiNER-shaped spans.
"""

from __future__ import annotations

import os
import sys
import types

import pytest


class _FakeGLiNER:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

    def predict_entities(self, text, labels, threshold=0.5, return_class_probs=False):
        # Echo back a span only for the "person" label, to prove the
        # kind<->label round trip and that unmapped labels are dropped.
        spans = []
        if "person" in labels:
            span = {"text": "Ada", "label": "person", "score": 0.95, "start": 0, "end": 3}
            if return_class_probs:
                # GLiNER keys probs by model label; "mystery" should be dropped
                # when mapped to EntityKind.
                span["class_probs"] = {"person": 0.95, "mystery": 0.05}
            spans.append(span)
        # An unmapped model label that classify() should drop.
        spans.append({"text": "x", "label": "mystery", "score": 0.9, "start": 4, "end": 5})
        return spans


@pytest.fixture(scope="module")
def client():
    # Clear the global prometheus registry so this module's service registers
    # its default metrics cleanly even when another service ran first in the
    # same process ("Duplicated timeseries").
    _reset_prometheus_registry()

    # resolve_model() needs NVISY_MODEL_NAME (served bentos inject it); the value
    # is irrelevant here since GLiNER is faked.
    os.environ["NVISY_MODEL_NAME"] = "fake/model"

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
    body = resp.json()[0]
    entities = body["entities"]
    # "person" span maps back to person_name; the unmapped "mystery" is dropped.
    assert len(entities) == 1
    assert entities[0]["kind"] == "person_name"
    assert (entities[0]["start"], entities[0]["end"]) == (0, 3)
    # provenance is on the response, default class_probs is omitted.
    assert body["modelId"] == "fake/model"
    assert entities[0].get("classProbs") is None


def test_class_probs_returned_and_mapped(client):
    resp = client.post(
        "/recognize",
        json={"requests": [{"text": "Ada", "kinds": ["person_name"], "returnClassProbs": True}]},
    )
    assert resp.status_code == 200
    probs = resp.json()[0]["entities"][0]["classProbs"]
    # keyed by EntityKind; the unmapped "mystery" label is dropped.
    assert probs == {"person_name": 0.95}


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
