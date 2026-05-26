# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), in
lockstep with the [Nvisy runtime](https://github.com/nvisycom/runtime).

## [Unreleased]

### Added

- uv workspace with the `nvisy-core`, `nvisy-ocr` (OCR), `nvisy-vl`
  (vision-language OCR), and `nvisy-ner` (NER) packages. Services are named
  for their purpose, not the engine, so the model can be swapped without
  changing the published image.
- v1 wire contract for OCR, vision-language OCR, and NER in `nvisy-core`, plus
  the shared `EntityCategory` / `EntityKind` taxonomy.
- docTR (OCR), PaddleOCR-VL (vision-language OCR), and GLiNER (NER) inference
  wired behind the `recognize` endpoints, with bring-your-own-weights via
  `NVISY_MODEL_PATH` / `/models`.
- Observability: per-service batch-size metric, and `x-request-id` correlation
  logging.
- OpenAPI specs and per-service requirements generated from the services into
  `docs/openapi/` and `packages/*/requirements.txt`.
- BentoML-native containerization (no hand-written Dockerfiles); `Makefile` for
  common tasks.
- CI: build, security (pip-audit), and release (GHCR images) workflows.
