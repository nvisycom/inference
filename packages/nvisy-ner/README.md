# nvisy-ner

BentoML NER service for nvisy — wraps **GLiNER** (official `gliner` package)
behind an HTTP/JSON endpoint. Request/response types come from
[`nvisy-core`](../nvisy-core).

> **Status:** scaffold. The model wiring lands in a follow-up.

## Develop

```bash
# from the repo root (uv workspace)
uv sync
uv run bentoml serve nvisy_ner.service:NerService --reload
```

## Endpoint (planned)

`POST /recognize` — text + zero-shot labels in, entities (label, score,
character offsets) out. Schema: [`nvisy_core.ner`](../nvisy-core/src/nvisy_core/ner.py);
exported under [`proto/`](../../proto).

## Bring your own weights

Mount custom GLiNER weights at `/models` (see the root README's docker-compose
example).
