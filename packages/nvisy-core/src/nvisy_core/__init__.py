"""Shared wire-contract types for the Nvisy inference services.

The contract is task-named and versioned:

- :mod:`nvisy_core.ocr` — OCR request/response (``Page → Block → Line → Word``).
- :mod:`nvisy_core.ner` — NER request/response (entities classified into the
  taxonomy).
- :mod:`nvisy_core.entity` — the :class:`~nvisy_core.entity.EntityCategory` and
  :class:`~nvisy_core.entity.EntityKind` taxonomy shared across services.

These mirror the Rust runtime (``nvisy-inference-client`` / ``nvisy-ontology``),
which is the source of truth; versioning is lockstep with the runtime.
"""

from nvisy_core import entity, ner, ocr

__all__ = ["entity", "ner", "ocr"]
