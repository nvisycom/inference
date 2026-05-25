# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), in
lockstep with the [Nvisy runtime](https://github.com/nvisycom/runtime).

## [Unreleased]

### Added

- uv workspace with the `nvisy-core`, `nvisy-paddle` (OCR), and `nvisy-gliner`
  (NER) packages.
- v1 wire contract for OCR and NER in `nvisy-core`, plus the shared
  `EntityCategory` / `EntityKind` taxonomy.
- PaddleOCR (PP-OCRv5) and GLiNER inference wired behind the `recognize`
  endpoints, with bring-your-own-weights via `NVISY_MODEL_PATH` / `/models`.
- Observability: per-service batch-size metric, and `x-request-id` correlation
  logging.
- OpenAPI specs and per-service requirements generated from the services into
  `docs/openapi/` and `packages/*/requirements.txt`.
- BentoML-native containerization (no hand-written Dockerfiles); `Makefile` for
  common tasks.
- CI: build, security (pip-audit), and release (GHCR images) workflows.
