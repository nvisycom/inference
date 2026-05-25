"""Mapping between GLiNER's free-text labels and the canonical entity taxonomy.

GLiNER is zero-shot: it takes arbitrary label strings at inference time and
returns the same strings on its spans. This module is the service's own
translation layer between those model-specific strings and
:class:`~nvisy_core.entity.EntityKind`:

- **request:** a requested :class:`EntityKind` -> the GLiNER label(s) to ask for.
- **response:** a GLiNER span's label -> the :class:`EntityKind` to report.

Owning this here is what makes the model swappable without a runtime change.
The default map mirrors the runtime's ``gliner-small-v2.1`` preset; a deployment
can override it (e.g. for BYO weights trained on different labels).
"""

from __future__ import annotations

from nvisy_core.entity import EntityKind

# kind -> the GLiNER label string we ask the model for. Mirrors the runtime
# preset's label_map (inverted: the runtime stores label -> kind).
DEFAULT_KIND_TO_LABEL: dict[EntityKind, str] = {
    EntityKind.PERSON_NAME: "person",
    EntityKind.GEOLOCATION_METADATA: "location",
    EntityKind.ORGANIZATION_NAME: "organization",
    EntityKind.EMAIL_ADDRESS: "email",
    EntityKind.PHONE_NUMBER: "phone number",
    EntityKind.DATE_TIME: "date",
    EntityKind.ADDRESS: "address",
}


class LabelMap:
    """Bidirectional map between GLiNER labels and entity kinds."""

    def __init__(self, kind_to_label: dict[EntityKind, str] | None = None) -> None:
        self._kind_to_label = dict(kind_to_label or DEFAULT_KIND_TO_LABEL)
        # Reverse lookup for classifying model output. If two kinds shared a
        # label the last one would win; the default map is 1:1.
        self._label_to_kind = {label: kind for kind, label in self._kind_to_label.items()}

    def labels_for(self, kinds: list[EntityKind]) -> list[str]:
        """The GLiNER labels to request for the given kinds (unmapped skipped)."""
        seen: dict[str, None] = {}
        for kind in kinds:
            label = self._kind_to_label.get(kind)
            if label is not None:
                seen.setdefault(label, None)
        return list(seen)

    def classify(self, label: str) -> EntityKind | None:
        """The kind for a GLiNER span label, or ``None`` if unmapped (dropped)."""
        return self._label_to_kind.get(label)


DEFAULT_LABEL_MAP = LabelMap()
