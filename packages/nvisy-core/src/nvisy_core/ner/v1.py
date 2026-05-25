"""NER wire contract, version 1.

Zero-shot named-entity recognition. The request supplies the entity *kinds* to
look for (from the canonical :class:`~nvisy_core.entity.EntityKind` taxonomy);
the service maps those to its model's labels, runs inference, and returns
matched entities classified back into the taxonomy. Because the service owns the
label mapping, swapping the underlying model never changes the wire contract.

The response carries the ``kind`` only — the :class:`EntityCategory` is
derivable from it (``kind.category``) and can never disagree.

The Rust runtime (``nvisy-inference-client``) is the source of truth; these
models mirror it. The wire is camelCase to match the runtime's serde
``rename_all = "camelCase"``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from nvisy_core.entity import EntityKind


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Entity(_Model):
    text: str = Field(description="The matched substring, text[start:end].")
    kind: EntityKind = Field(description="The canonical kind this entity was classified as.")
    score: float = Field(ge=0.0, le=1.0)
    start: int = Field(ge=0, description="Character offset, inclusive.")
    end: int = Field(ge=0, description="Character offset, exclusive.")


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
    language: str | None = Field(
        default=None,
        description="BCP-47 language hint (advisory).",
    )


class NerResponse(_Model):
    entities: list[Entity] = Field(default_factory=list)
