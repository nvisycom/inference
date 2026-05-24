# nvisy-ocr

BentoML OCR service for nvisy — wraps **PaddleOCR PP-OCRv5** (official
`paddleocr` package) behind an HTTP/JSON endpoint. Request/response types come
from [`nvisy-core`](../nvisy-core).

> **Status:** scaffold. The model wiring lands in a follow-up.

## Develop

```bash
# from the repo root (uv workspace)
uv sync
uv run bentoml serve nvisy_ocr.service:OcrService --reload
```

## Endpoint (planned)

`POST /recognize` — image in, `Page → Block → Line → Word` JSON out. Schema:
[`nvisy_core.ocr`](../nvisy-core/src/nvisy_core/ocr.py); exported under
[`proto/`](../../proto).

## Bring your own weights

Mount custom PaddleOCR weights at `/models` (see the root README's
docker-compose example).
