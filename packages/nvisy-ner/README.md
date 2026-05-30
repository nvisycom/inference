# nvisy-ner

[![Build](https://img.shields.io/github/actions/workflow/status/nvisycom/inference/build.yml?branch=main&label=build%20%26%20test&style=flat-square)](https://github.com/nvisycom/inference/actions/workflows/build.yml)

Default NER inference service for nvisy. Wraps
[GLiNER](https://github.com/urchade/GLiNER) behind an HTTP/JSON endpoint,
published as `ghcr.io/nvisy/inference-ner`.

## Overview

`NerService` exposes a single `POST /recognize` endpoint that takes text plus a
set of entity kinds and returns matched entities — each with a kind, score, and
character offsets. It is the default implementation of the NER wire contract —
request and response types come from [`nvisy_core.ner.v1`](../nvisy-core), and
the generated contract lives at [`docs/openapi/ner.json`](../../docs/openapi/ner.json).
Any service that speaks the same contract can replace it
(bring-your-own-inference).

The service maps requested kinds to GLiNER's labels (and back) via its
[`label_map`](src/nvisy_ner/label_map.py), so the model stays an
implementation detail behind the taxonomy.

BentoML batches concurrent calls, so the HTTP body wraps the list:
`{"requests": [ { "text": ..., "kinds": ["person_name"], "threshold": 0.5 } ]}`;
the response is a JSON array of `NerResponse`.

### Configuration

- `NVISY_MODEL_PATH` — filesystem path to GLiNER weights. Takes precedence; also
  satisfied by mounting weights at `/models`.
- `NVISY_MODEL_NAME` — model id to load/download when no path is given (e.g.
  `knowledgator/gliner-pii-large-v1.0`). Defaults to `urchade/gliner_multi-v2.1`.
- `LOG_LEVEL` — logging level (default `INFO`).

```bash
uv sync
uv run bentoml serve nvisy_ner.service:NerService --reload
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
