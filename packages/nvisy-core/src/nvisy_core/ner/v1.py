"""NER wire contract, version 1.

Zero-shot named-entity recognition. The request supplies the entity *kinds* to
look for (from the canonical :class:`~nvisy_core.entity.EntityKind` taxonomy);
the service maps those to its model's labels, runs inference, and returns
matched entities classified back into the taxonomy. Because the service owns the
label mapping, swapping the underlying model never changes the wire contract.

Each entity carries the ``kind`` only — the :class:`EntityCategory` is derivable
from it (``kind.category``) and can never disagree — plus, when requested, the
per-kind probability distribution (``classProbs``). The response also reports
the ``modelId`` that produced the entities, for provenance.

The Rust runtime (``nvisy-inference-client``) is the source of truth; these
models mirror it. The wire is camelCase to match the runtime's serde
``rename_all = "camelCase"``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from nvisy_core.entity import EntityKind


class _Model(BaseModel):
    # camelCase on the wire: aliases on input (populate_by_name accepts either)
    # AND on output (serialize_by_alias) so responses match the OpenAPI schema.
    # protected_namespaces=(): allow fields like `model_id`.
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        protected_namespaces=(),
    )


class Entity(_Model):
    text: str = Field(description="The matched substring, text[start:end].")
    kind: EntityKind = Field(description="The canonical kind this entity was classified as.")
    score: float = Field(ge=0.0, le=1.0)
    start: int = Field(ge=0, description="Character offset, inclusive.")
    end: int = Field(ge=0, description="Character offset, exclusive.")
    class_probs: dict[EntityKind, float] | None = Field(
        default=None,
        description="Per-kind probability distribution for this span, mapped from "
        "the model's labels. Present only when the request set "
        "returnClassProbs; kinds outside the request are omitted.",
    )

    @model_validator(mode="after")
    def _check_span(self) -> Entity:
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class NerRequest(_Model):
    text: str
    kinds: list[EntityKind] = Field(
        min_length=1,
        description="Entity kinds to extract. The service maps these to its model's labels.",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum score for an entity to be returned.",
    )
    return_class_probs: bool = Field(
        default=False,
        description="Include the per-kind probability distribution on each entity.",
    )


class NerResponse(_Model):
    entities: list[Entity] = Field(default_factory=list)
    model_id: str = Field(
        description="Identifier of the model that produced these entities "
        "(e.g. the loaded GLiNER repo id). Lets the runtime attribute "
        "recognition provenance without hardcoding it.",
    )
