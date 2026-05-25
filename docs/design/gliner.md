# GLiNER — why we use it for NER

`nvisy-gliner` is the default NER engine. It detects named entities (people,
emails, IBANs, …) in text and is the source of the entity spans the runtime
redacts.

## Why GLiNER

- **Zero-shot.** GLiNER takes the entity types to look for as *labels at
  inference time* — it is not locked to a fixed label set. We ask for the
  canonical [`EntityKind`](../../packages/nvisy-core/src/nvisy_core/entity.py)
  types we care about, and the service maps those to GLiNER's label strings (and
  back) via its
  [`label_map`](../../packages/nvisy-gliner/src/nvisy_gliner/label_map.py). New
  entity kinds need no retraining — just a label.
- **Small and CPU-viable.** A compact encoder model that runs comfortably on CPU,
  fitting the self-hosted footprint the ADR targets. No GPU required.
- **Multilingual.** The default `urchade/gliner_multi-v2.1` handles many
  languages out of the box.
- **Character-offset spans.** Returns `start`/`end` character offsets, exactly
  what the redaction pipeline needs to locate and mask a span in text.

## What it gives us

Per recognized span: the matched text, the `EntityKind` (classified from
GLiNER's label via the label map), a confidence score, character offsets, and —
on request — the per-kind probability distribution (`classProbs`). The contract
lives in [`nvisy_core.ner.v1`](../../packages/nvisy-core/src/nvisy_core/ner/v1.py).

## What it is *not*

- **Not a pattern matcher.** Structured PII with strong syntactic signals
  (credit-card Luhn, API keys, private keys) is better caught by deterministic
  patterns in the runtime; GLiNER covers them but is weaker than regex/checksum
  there.
- **Not coreference / linking.** GLiNER returns independent spans — no entity
  IDs, no cross-span clustering. (Confirmed against its output; we do not expose
  fields it cannot produce.)
- **Not for non-text modalities.** Visual/biometric kinds (faces, signatures,
  barcodes) are out of scope — they belong to the OCR/CV path, and the label map
  deliberately omits them.

## Swappability

The label map makes the model an implementation detail: a deployment can bring
its own GLiNER weights (or a different NER model) and remap labels without any
change to the wire contract or the runtime.
