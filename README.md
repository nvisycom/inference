# Nvisy Inference

[![Build](https://img.shields.io/github/actions/workflow/status/nvisycom/inference/build.yml?branch=main&label=build%20%26%20test&style=flat-square)](https://github.com/nvisycom/inference/actions/workflows/build.yml)

Externalized model inference for the [Nvisy runtime](https://github.com/nvisycom/runtime).

Hosts each model as a standalone HTTP/JSON service so the runtime calls
inference over the network instead of loading ML runtimes in-process. See the
ADR: [nvisycom/runtime#194](https://github.com/nvisycom/runtime/issues/194).

## Overview

Two [BentoML](https://bentoml.com) services, packaged as independent images.
They are the **default** implementations of the OCR and NER wire contracts —
named after the engine they wrap, since the contract (not the engine) is what
the runtime depends on:

- **`nvisy-paddle`** ([`packages/nvisy-paddle`](packages/nvisy-paddle)) —
  PaddleOCR PP-OCRv5 (OCR contract), published as `ghcr.io/nvisy/inference-paddle`.
- **`nvisy-gliner`** ([`packages/nvisy-gliner`](packages/nvisy-gliner)) —
  GLiNER (NER contract), published as `ghcr.io/nvisy/inference-gliner`.

Two containers, not one: independent scaling, independent failure domains, and
customers can opt out of either.

The HTTP/JSON wire contract is **our shape, not BentoML's**. The pydantic types
in [`nvisy-core`](packages/nvisy-core) are the contract; BentoML is just the
reference implementation. Anything that speaks the contract can be dropped in
(bring-your-own-inference). Machine-readable OpenAPI specs are generated from
the services into [`docs/openapi/`](docs/openapi). The Rust runtime
(`nvisy-inference-client`) is the source of truth; versioning is lockstep —
runtime `vX.Y.Z` expects inference `vX.Y.Z`.

The repository is a single [uv](https://docs.astral.sh/uv/) workspace: all
packages share one lockfile and resolve `nvisy-core` locally, while each service
still ships only its own dependency subtree. Python is pinned to 3.12
(PaddlePaddle has no 3.13 wheels yet).

Images are built by BentoML itself (`bentoml build` + `containerize`) from the
`Image` config in each `service.py` — there are no hand-written Dockerfiles. The
per-service `requirements.txt` is exported from the workspace lock
(`scripts/gen_requirements.py`).

Common tasks are wrapped in the [`Makefile`](Makefile) (`make help` to list):

```bash
make bento            # install BentoML + workspace deps
make serve-paddle     # serve the OCR service locally (or serve-gliner)
make build            # build both Bentos
make containerize     # build + containerize into local Docker images
make generate         # regenerate OpenAPI specs + per-service requirements
make ci               # lint + drift checks + tests
```

## Deploy

```yaml
services:
  inference-paddle:
    image: ghcr.io/nvisy/inference-paddle:1.0
    volumes:
      - ./my-paddleocr-weights:/models   # optional: BYO weights
  inference-gliner:
    image: ghcr.io/nvisy/inference-gliner:1.0
    volumes:
      - ./my-gliner-weights:/models      # optional: BYO weights
```

## Documentation

See [`docs/`](docs/) for the generated OpenAPI specs and contract documentation.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.

## License

Apache 2.0 License, see [LICENSE.txt](LICENSE.txt)

## Support

- **Documentation**: [docs.nvisy.com](https://docs.nvisy.com)
- **Issues**: [GitHub Issues](https://github.com/nvisycom/inference/issues)
- **Email**: [support@nvisy.com](mailto:support@nvisy.com)
