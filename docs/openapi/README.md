# OpenAPI specs

Machine-readable wire contracts for the inference services, **generated** from
the BentoML services — do not edit by hand.

- [`ocr.json`](ocr.json) — OCR contract (default impl: `nvisy-ocr`, docTR).
- [`ner.json`](ner.json) — NER contract (default impl: `nvisy-ner`, GLiNER).
- [`vl.json`](vl.json) — vision-language OCR contract (default impl:
  `nvisy-vl`, PaddleOCR-VL).

Regenerate after changing the `nvisy-core` types or a service signature:

```bash
uv run python scripts/gen_openapi.py
```

CI fails if these drift from the services (`gen_openapi.py --check`). They are
the contract for bring-your-own-inference implementers.
