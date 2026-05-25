"""NER wire contract, version 1.

Zero-shot named-entity recognition: the request supplies the candidate
``labels`` at inference time (GLiNER is label-agnostic), and the response
returns matched entities with a label, score, and character offsets into the
request text.

The Rust runtime (``nvisy-inference-client``) is the source of truth; these
models mirror it. The wire is camelCase to match the runtime's serde
``rename_all = "camelCase"``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Entity(_Model):
    text: str = Field(description="The matched substring, text[start:end].")
    label: str = Field(description="The requested label this entity matched.")
    score: float = Field(ge=0.0, le=1.0)
    start: int = Field(ge=0, description="Character offset, inclusive.")
    end: int = Field(ge=0, description="Character offset, exclusive.")


class NerRequest(_Model):
    text: str
    labels: list[str] = Field(
        min_length=1,
        description="Zero-shot entity labels to extract (lower/title case).",
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
