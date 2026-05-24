# nvisy-core

Shared wire-contract schema for the nvisy inference services. The OCR and NER
services both depend on this package for their request/response types, so the
HTTP contract is defined in exactly one place on the Python side.

> Per the ADR ([nvisycom/runtime#194](https://github.com/nvisycom/runtime/issues/194)),
> the Rust runtime (`nvisy-inference-client`) is the ultimate source of truth;
> these models mirror it. JSON Schemas are exported under [`../../proto/`](../../proto).

## Modules

- `nvisy_core.ocr` — OCR contract (`Page → Block → Line → Word`).
- `nvisy_core.ner` — NER contract (`Entity` with labels, score, char offsets).

> **Status:** scaffold. Types below are illustrative placeholders, finalized in
> the contract-design follow-up.
