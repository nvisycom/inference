# nvisy-gliner

[![Build](https://img.shields.io/github/actions/workflow/status/nvisycom/inference/build.yml?branch=main&label=build%20%26%20test&style=flat-square)](https://github.com/nvisycom/inference/actions/workflows/build.yml)

Default NER inference service for nvisy. Wraps GLiNER behind an HTTP/JSON
endpoint, published as `ghcr.io/nvisy/inference-gliner`.

## Overview

`NerService` exposes a single `POST /recognize` endpoint that takes text plus a
set of zero-shot labels and returns matched entities — each with a label, score,
and character offsets. It is the default implementation of the NER wire contract
— request and response types come from [`nvisy_core.ner.v1`](../nvisy-core), and
the generated contract lives at [`docs/openapi/ner.json`](../../docs/openapi/ner.json).
Any service that speaks the same contract can replace it
(bring-your-own-inference).

Model weights load on startup. Mount custom GLiNER weights at `/models` to bring
your own (see the repository [README](../../README.md) deploy example).

> **Status:** scaffold. The endpoint is wired to the v1 contract; GLiNER
> inference is filled in by a follow-up.

```bash
uv sync
uv run bentoml serve nvisy_gliner.service:NerService --reload
```

## Documentation

See [`docs/`](../../docs/) for the generated OpenAPI specs and contract
documentation.

## Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for release notes and version history.

## License

Apache 2.0 License, see [LICENSE.txt](../../LICENSE.txt)

## Support

- **Documentation**: [docs.nvisy.com](https://docs.nvisy.com)
- **Issues**: [GitHub Issues](https://github.com/nvisycom/inference/issues)
- **Email**: [support@nvisy.com](mailto:support@nvisy.com)
