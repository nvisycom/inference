"""NER wire contract: zero-shot entities with labels, score, char offsets.

Scaffold stub — finalized in the contract-design follow-up and kept in sync
with the Rust source of truth (``nvisy-inference-client``).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NerRequest(_Model):
    text: str
    labels: list[str] = Field(description="Zero-shot entity labels to extract.")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class Entity(_Model):
    text: str
    label: str
    score: float
    start: int = Field(description="Character offset (inclusive).")
    end: int = Field(description="Character offset (exclusive).")


class NerResponse(_Model):
    entities: list[Entity] = Field(default_factory=list)
