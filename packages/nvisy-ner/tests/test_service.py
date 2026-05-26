"""Smoke tests for the NER service scaffold."""

import bentoml
import pytest
from nvisy_core.entity import EntityCategory, EntityKind
from nvisy_core.ner.v1 import Entity, NerRequest, NerResponse
from nvisy_ner.label_map import DEFAULT_KIND_TO_LABEL, DEFAULT_LABEL_MAP, LabelMap
from nvisy_ner.service import NerService


def test_request_takes_entity_kinds():
    req = NerRequest(text="hi", kinds=[EntityKind.PERSON_NAME], threshold=0.3)
    assert req.kinds == [EntityKind.PERSON_NAME]


def test_entity_carries_kind_and_offsets():
    ent = Entity(text="Ada", kind=EntityKind.PERSON_NAME, score=0.9, start=0, end=3)
    assert (ent.start, ent.end) == (0, 3)
    assert ent.kind.category == EntityCategory.PERSONAL_IDENTITY


def test_entity_rejects_non_positive_span():
    import pytest

    with pytest.raises(ValueError, match="end must be greater than start"):
        Entity(text="", kind=EntityKind.PERSON_NAME, score=0.9, start=3, end=3)


def test_response_serializes_kind_and_model_id():
    resp = NerResponse(
        entities=[Entity(text="Ada", kind=EntityKind.PERSON_NAME, score=0.9, start=0, end=3)],
        model_id="org/some-model",
    )
    dumped = resp.model_dump(by_alias=True, mode="json")
    assert dumped["entities"][0]["kind"] == "person_name"
    assert dumped["modelId"] == "org/some-model"


def test_label_map_round_trips():
    # kind -> label -> kind
    labels = DEFAULT_LABEL_MAP.labels_for([EntityKind.PERSON_NAME, EntityKind.EMAIL_ADDRESS])
    assert labels == ["person", "email"]
    assert DEFAULT_LABEL_MAP.classify("person") == EntityKind.PERSON_NAME
    assert DEFAULT_LABEL_MAP.classify("unmapped-label") is None


# Visual/biometric kinds aren't text-detectable, so GLiNER can't find them.
_NON_TEXT_KINDS = {
    EntityKind.FACE,
    EntityKind.FINGERPRINT,
    EntityKind.VOICEPRINT,
    EntityKind.RETINA_SCAN,
    EntityKind.FACIAL_GEOMETRY,
    EntityKind.HANDWRITING,
    EntityKind.SIGNATURE,
    EntityKind.LOGO,
    EntityKind.BARCODE,
    EntityKind.UNRESOLVED,
}


def test_label_map_covers_all_text_kinds():
    mapped = set(DEFAULT_KIND_TO_LABEL)
    expected = set(EntityKind) - _NON_TEXT_KINDS
    assert mapped == expected, f"missing: {expected - mapped}, unexpected: {mapped - expected}"


def test_label_map_omits_non_text_kinds():
    assert _NON_TEXT_KINDS.isdisjoint(DEFAULT_KIND_TO_LABEL)


def test_label_map_labels_are_unique():
    labels = list(DEFAULT_KIND_TO_LABEL.values())
    assert len(labels) == len(set(labels)), "label strings must be 1:1 for reverse mapping"


def test_label_map_rejects_non_injective_mapping():
    with pytest.raises(ValueError, match="must be injective"):
        LabelMap({EntityKind.PERSON_NAME: "x", EntityKind.USERNAME: "x"})


def test_labels_for_dedupes_and_skips_unmapped():
    # FACE has no mapping (visual); PERSON_NAME requested twice dedupes.
    labels = DEFAULT_LABEL_MAP.labels_for(
        [EntityKind.PERSON_NAME, EntityKind.FACE, EntityKind.PERSON_NAME]
    )
    assert labels == ["person"]


def test_service_exposes_recognize_endpoint():
    assert isinstance(NerService, bentoml.Service)
    assert NerService.name == "nvisy-inference-ner"
    assert "recognize" in NerService.apis
