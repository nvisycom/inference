"""Smoke tests for the NER service scaffold."""

import bentoml
from nvisy_core.ner import Entity, NerRequest
from nvisy_ner.service import NerService


def test_request_model_validates():
    req = NerRequest(text="hi", labels=["person"], threshold=0.3)
    assert req.labels == ["person"]


def test_entity_offsets_are_ints():
    ent = Entity(text="Ada", label="person", score=0.9, start=0, end=3)
    assert (ent.start, ent.end) == (0, 3)


def test_service_exposes_recognize_endpoint():
    assert isinstance(NerService, bentoml.Service)
    assert NerService.name == "nvisy-inference-ner"
    assert "recognize" in NerService.apis
