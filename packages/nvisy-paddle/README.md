# nvisy-paddle

[![Build](https://img.shields.io/github/actions/workflow/status/nvisycom/inference/build.yml?branch=main&label=build%20%26%20test&style=flat-square)](https://github.com/nvisycom/inference/actions/workflows/build.yml)

Default OCR inference service for nvisy. Wraps PaddleOCR PP-OCRv5 behind an
HTTP/JSON endpoint, published as `ghcr.io/nvisy/inference-paddle`.

## Overview

`OcrService` exposes a single `POST /recognize` endpoint that takes a
base64-encoded image and returns a `Page → Block → Line → Word` hierarchy. It is
the default implementation of the OCR wire contract — request and response types
come from [`nvisy_core.ocr.v1`](../nvisy-core), and the generated contract lives
at [`docs/openapi/ocr.json`](../../docs/openapi/ocr.json). Any service that
speaks the same contract can replace it (bring-your-own-inference).

BentoML batches concurrent calls, so the HTTP body wraps the list:
`{"requests": [ { "image": "<base64>", "confidenceThreshold": 0.5 } ]}`; the
response is a JSON array of `OcrResponse`.

### Configuration

- `NVISY_MODEL_PATH` — path to PaddleOCR weights. Defaults to `/models` when
  that mount is non-empty, otherwise downloads the PP-OCRv5 English models.
- `LOG_LEVEL` — logging level (default `INFO`).

```bash
uv sync
uv run bentoml serve nvisy_paddle.service:OcrService --reload
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
