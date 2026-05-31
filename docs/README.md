# Documentation

Reference documentation for the Nvisy inference services.

## Contents

- [`openapi/`](openapi) — machine-readable OpenAPI specs, **generated** from the
  services (`scripts/gen_openapi.py`). The wire contract for
  bring-your-own-inference.
- [`design/`](design) — per-engine rationale: why we chose the model behind each
  service ([docTR](design/tocr.md), [GLiNER](design/gliner.md),
  [PaddleOCR-VL](design/ocrvlm.md)) and what would replace it.

## Wire contract

The contract is defined as pydantic types in
[`nvisy-core`](../packages/nvisy-core) and is task-named (OCR, vision-language
OCR, NER), independent of the engine that implements it:

| Module | Purpose |
| --- | --- |
| [`nvisy_core.ocr.v1`](../packages/nvisy-core/src/nvisy_core/ocr/v1.py) | OCR request/response — `Page → Block → Line → Word` with word-level geometry. |
| [`nvisy_core.ocrvl.v1`](../packages/nvisy-core/src/nvisy_core/ocrvl/v1.py) | Vision-language OCR request/response — block-level regions with text, layout kind, bbox, and reading order. |
| [`nvisy_core.ner.v1`](../packages/nvisy-core/src/nvisy_core/ner/v1.py) | NER request/response — entities classified into the taxonomy. |
| [`nvisy_core.entity`](../packages/nvisy-core/src/nvisy_core/entity.py) | `EntityCategory` / `EntityKind` taxonomy. |

### Entity taxonomy

NER responses carry an `EntityKind` (one of 65 canonical kinds), not a raw model
label. Each kind belongs to exactly one of 13 `EntityCategory` buckets, derivable
via `kind.category`, so the wire carries only the kind. Services own the mapping
between their model's labels and these kinds (e.g.
[`nvisy_ner.label_map`](../packages/nvisy-ner/src/nvisy_ner/label_map.py)),
which is what lets the model be swapped without a runtime change.

The taxonomy mirrors the Rust runtime's `nvisy-ontology` enums, which are the
ultimate source of truth; versioning is lockstep with the runtime.

## Regenerating

```bash
uv run python scripts/gen_openapi.py   # rewrite docs/openapi/*.json
```

CI fails if the committed specs drift from the services.
