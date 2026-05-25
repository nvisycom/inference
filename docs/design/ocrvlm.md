# OCR VLM — why we (will) add a vision-language layer

> Status: **planned**, not yet implemented. This explains why a VLM belongs in
> the OCR story and how it relates to the traditional OCR engine.

A vision-language model (e.g. PaddleOCR-VL, Qwen3-VL) reads a document image and
produces text — often with superior accuracy on hard inputs — plus structure and
reading order. We plan to add it as an **optional verification/refinement layer**
on top of traditional OCR, not as a replacement.

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
the VLM ships as its **own opt-in GPU service** (`nvisy-vl`), not bundled into
the CPU OCR container — independent scaling and failure domains, and CPU-only
deployments simply don't run it. The runtime orchestrates: it calls the OCR
service for geometry+text and, when verification is requested, the VLM service,
then reconciles them.

## Open questions (resolve before building)

- Does the chosen VLM expose per-region boxes usable for aligning its text back
  to OCR regions, or only document-level Markdown/JSON? (Determines the
  reconciliation strategy.)
- Box/word-level precision and real footprint of candidate VLMs.
- The confidence signal that triggers per-region verification.

## Candidates

- **PaddleOCR-VL** — compact (~0.9B), 109 languages, emits 4-point quads + text +
  structure + reading order; strong throughput.
- **Qwen3-VL** — general-purpose VLM with grounding; larger, slower for OCR.

The contract is ours, so the VLM is swappable like every other engine.
