# nvisy/inference

Model inference for [nvisy](https://github.com/nvisycom/runtime), externalized
into standalone HTTP/JSON services. The Rust runtime calls these over HTTP
instead of loading ML runtimes in-process.

See the ADR: [nvisycom/runtime#194](https://github.com/nvisycom/runtime/issues/194).

## Services

| Package | Model | Image |
| --- | --- | --- |
| [`packages/nvisy-ocr`](packages/nvisy-ocr) | PaddleOCR PP-OCRv5 | `ghcr.io/nvisy/inference-ocr` |
| [`packages/nvisy-ner`](packages/nvisy-ner) | GLiNER | `ghcr.io/nvisy/inference-ner` |

Both built on [BentoML](https://bentoml.com) and sharing the wire-contract types
in [`packages/nvisy-core`](packages/nvisy-core).

Two containers, not one: independent scaling, independent failure domains, and
customers can opt out of either.

## The contract is the product

The HTTP/JSON wire contract is **our shape, not BentoML's**. BentoML is just the
reference implementation — anything that speaks the schema in
[`proto/`](proto) can be dropped in (FastAPI, Triton, your own). That's the
bring-your-own-inference (BYOI) exit hatch. The Rust runtime
(`nvisy-inference-client`) is the source of truth; these services mirror it.

Versioning is lockstep: runtime `vX.Y.Z` expects inference `vX.Y.Z`.

## Layout

```
inference/
├── packages/
│   ├── nvisy-core/   # shared wire-contract schema (pydantic types)
│   ├── nvisy-ocr/    # PaddleOCR service (depends on nvisy-core)
│   └── nvisy-ner/    # GLiNER service    (depends on nvisy-core)
├── docker/           # ocr.Dockerfile, ner.Dockerfile (context = repo root)
├── proto/            # versioned JSON schemas (the wire contract)
├── pyproject.toml    # uv workspace root + shared ruff/pytest config
└── .github/          # dependabot + build / security / release workflows
```

A single [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
all packages share one lockfile and resolve `nvisy-core` locally. The two
services still ship as **separate images** (independent failure domains), each
baking only its own dependency subtree.

## Develop

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12 (PaddlePaddle has no
3.13 wheels yet).

```bash
uv sync                                                  # whole workspace
uv run bentoml serve nvisy_ocr.service:OcrService --reload
uv run bentoml serve nvisy_ner.service:NerService --reload
```

## Deploy

```yaml
services:
  inference-ocr:
    image: ghcr.io/nvisy/inference-ocr:1.0
    volumes:
      - ./my-paddleocr-weights:/models   # optional: BYO weights
  inference-ner:
    image: ghcr.io/nvisy/inference-ner:1.0
    volumes:
      - ./my-gliner-weights:/models      # optional: BYO weights
```

## License

Apache-2.0.
