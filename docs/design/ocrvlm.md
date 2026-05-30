# OCR VLM — the vision-language verification layer

> Status: **shipped** as [`nvisy-vl`](../../packages/nvisy-vl)
> (PaddleOCR-VL). This explains why a VLM belongs in the OCR story and how it
> relates to the traditional OCR engine.

A vision-language model (e.g. PaddleOCR-VL, Qwen3-VL) reads a document image and
produces text — often with superior accuracy on hard inputs — plus structure and
reading order. We add it as an **optional verification/refinement layer** on top
of traditional OCR, not as a replacement.

## Why a VLM at all

Traditional OCR ([docTR](tocr.md)) gives precise geometry but can misread:

- handwriting and low-quality scans,
- dense or complex multilingual text,
- unusual fonts and layouts.

VLMs are markedly better at *transcription accuracy* in these cases. Better text
means better downstream entity detection (and thus redaction).

## Why a layer, not a replacement

The division of labor is the whole point:

- **Traditional OCR owns geometry** (*where* the text is) — pixel-precise word
  boxes for masking. This is a VLM's relative weakness: VLM coordinates are
  looser, and we should not bet mask precision on them.
- **The VLM owns text content** (*what* the text says) — refining/correcting the
  transcription within the boxes the OCR engine already found.

So geometry is never taken from the VLM; it only improves text.

## Why conservative refinement

Research (*"VLMs Are Not (Yet) Spelling Correctors"*, arXiv 2509.17418) shows
blindly trusting a VLM's "corrected" text can *hurt* — VLMs hallucinate. So the
refinement is a **Joint OCR–Correction** policy: accept a VLM correction only
when it is a bounded edit (low Levenshtein distance) of the OCR text; keep the
original otherwise. Prefer running the VLM only on low-confidence regions.

## Why a separate, opt-in service

A 0.9B+ VLM wants a GPU and busts the CPU footprint the OCR service targets. So
the VLM ships as its **own opt-in GPU service** (`nvisy-vl`), not bundled
into the CPU OCR container — independent scaling and failure domains, and
CPU-only deployments simply don't run it. The runtime orchestrates: it calls the
OCR service for geometry+text and, when verification is requested, the VLM
service, then reconciles them.

## Resolved questions

- **Per-region boxes?** PaddleOCR-VL emits a 4-point quad + axis-aligned bbox per
  parsed block (`parsing_res_list`), in reading order — verified live. The
  service surfaces these as `Region.bbox`. They are usable for *aligning* a
  region's text to OCR geometry, but not precise enough to *replace* it; word
  boxes still come from docTR.
- **Footprint.** PaddleOCR-VL is ~0.9B and Apache-2.0 — the reason it's the
  default VL backend (see candidates).

## Still open

- The confidence signal that triggers per-region verification (vs. always-on).
  Lives in the runtime's reconciliation, not this service.

## Candidates

- **PaddleOCR-VL** *(shipped default)* — compact (~0.9B), 109 languages,
  **Apache-2.0**. Emits 4-point quads + axis-aligned bbox + text + structure +
  reading order; strong throughput; runs on CPU (slow) or GPU.
- **Chandra OCR 2** — 5B (Qwen-based), strongest *text* of the candidates
  (handwriting, forms, math, 90+ langs) and **does produce per-region layout
  boxes** (around figures/tables — surfaced via its `chunks` output, which is
  typed only as a loose dict; the strongly-typed schema guarantees only a
  page-level `page_box`). Not the default for two reasons that are decisive for a
  commercial product: **license** — weights are modified OpenRAIL-M (free only
  under ~$2M revenue and forbidden from competing with Datalab's API; quantized
  2B/8B are commercial-only), and **footprint** — 5B, GPU-only (~2 pages/s on an
  H100) vs. 0.9B. A viable *premium opt-in* backend only if the license is
  cleared and the GPU cost is accepted.
- **Qwen3-VL** — general-purpose VLM with grounding; larger, slower for OCR.

The contract is ours, so the VLM is swappable like every other engine — Chandra
or Qwen3-VL could be dropped in behind the same `ocrvl` contract.
