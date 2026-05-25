"""Smoke tests for the NER service scaffold."""

import bentoml
from nvisy_core.entity import EntityCategory, EntityKind
from nvisy_core.ner.v1 import Entity, NerRequest, NerResponse
from nvisy_gliner.label_map import DEFAULT_LABEL_MAP
from nvisy_gliner.service import NerService


def test_request_takes_entity_kinds():
    req = NerRequest(text="hi", kinds=[EntityKind.PERSON_NAME], threshold=0.3)
    assert req.kinds == [EntityKind.PERSON_NAME]


def test_entity_carries_kind_and_offsets():
    ent = Entity(text="Ada", kind=EntityKind.PERSON_NAME, score=0.9, start=0, end=3)
    assert (ent.start, ent.end) == (0, 3)
    assert ent.kind.category == EntityCategory.PERSONAL_IDENTITY


def test_response_serializes_kind_as_snake_case():
    resp = NerResponse(
        entities=[Entity(text="Ada", kind=EntityKind.PERSON_NAME, score=0.9, start=0, end=3)]
    )
    dumped = resp.model_dump(by_alias=True, mode="json")
    assert dumped["entities"][0]["kind"] == "person_name"


def test_label_map_round_trips():
    # kind -> label -> kind
    labels = DEFAULT_LABEL_MAP.labels_for([EntityKind.PERSON_NAME, EntityKind.EMAIL_ADDRESS])
    assert labels == ["person", "email"]
    assert DEFAULT_LABEL_MAP.classify("person") == EntityKind.PERSON_NAME
    assert DEFAULT_LABEL_MAP.classify("unmapped-label") is None


def test_service_exposes_recognize_endpoint():
    assert isinstance(NerService, bentoml.Service)
    assert NerService.name == "nvisy-inference-gliner"
    assert "recognize" in NerService.apis
