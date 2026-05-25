"""Smoke tests for the NER service scaffold."""

import bentoml
from nvisy_core.ner.v1 import Entity, NerRequest, NerResponse
from nvisy_gliner.service import NerService


def test_request_model_validates():
    req = NerRequest(text="hi", labels=["person"], threshold=0.3)
    assert req.labels == ["person"]


def test_entity_offsets_are_ints():
    ent = Entity(text="Ada", label="person", score=0.9, start=0, end=3)
    assert (ent.start, ent.end) == (0, 3)


def test_response_round_trips_camel_case():
    resp = NerResponse(entities=[Entity(text="Ada", label="person", score=0.9, start=0, end=3)])
    dumped = resp.model_dump(by_alias=True)
    assert dumped["entities"][0]["label"] == "person"


def test_service_exposes_recognize_endpoint():
    assert isinstance(NerService, bentoml.Service)
    assert NerService.name == "nvisy-inference-gliner"
    assert "recognize" in NerService.apis
