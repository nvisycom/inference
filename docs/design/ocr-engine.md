# Design: OCR engine — options and decision

> Status: **investigation**. This is a decision doc, not a committed design. It
> captures the candidate OCR architectures, what each gives us, the open
> questions, and a spike plan to choose. Leaning candidate: **docTR (word
> geometry) + a VLM (text accuracy)** — pending the spike.

## Problem

The OCR service runs basic PaddleOCR PP-OCRv5, which returns a **flat list of
line-level boxes** — no layout structure (blocks, reading order), and PaddleOCR
is **weak at word-level boxes** (detection is line-level; `return_word_box`
derives word boxes post-rectification and degrades on rotation). Our wire
contract promises `Page → Block → Line → Word`, so today the service emits a
degenerate one-block/one-line page.

Redaction has two hard requirements:

1. **Word-level geometry** — to mask a *sub-line* span (e.g. just an SSN inside a
   line), we need per-word (ideally per-character) boxes, not just line boxes.
   NER gives character offsets; turning "chars 12–23 of this line" into a pixel
   mask needs word/char geometry.
2. **Accurate text content** — so downstream entity detection is reliable,
   including on messy/handwritten/multilingual input where classic OCR struggles.

No single classic model does both well: PaddleOCR is strong on structure/tables
but weak on word boxes; VLMs are strong on text accuracy but historically loose
on geometry.

## What changed during investigation

Two findings reshaped the options:

- **PaddleOCR-VL 1.5 *does* emit geometry** — 8 `<|LOC_nnn|>` tokens per region
  (a 4-point quad on a normalized 0–999 grid), plus text + structure + reading
  order in a single forward pass (94.5% OmniDocBench, faster than pipeline
  alternatives). **But** a user reports its JSON bbox coordinates don't directly
  match PDF crops (coordinate-space mapping needed) — a red flag for
  mask-precise use until verified.
- **docTR gives native word/char/line boxes** — exactly PaddleOCR's weak spot
  and redaction's need.

So the original "PP-StructureV3 for geometry + VL for text" framing is no longer
obviously right: the geometry source is now an open choice.

## Candidate architectures

### A. docTR (geometry) + VLM (text accuracy) — *leaning candidate*

- **docTR** owns geometry: native word/line/block boxes (its strength, our need).
- A **VLM** (PaddleOCR-VL or Qwen3-VL) refines/verifies the *text* within docTR's
  boxes. Geometry always from docTR; VL never owns coordinates.
- Plays each tool to its strength; mixes vendors (acceptable — the contract is
  ours, engines are swappable, per the workspace philosophy).
- Cost: two models; VL is GPU-heavy; reconciliation needed (see below).

### B. PaddleOCR-VL 1.5 alone

- One fast pass → boxes (quads) + text + structure + reading order, 109 langs.
- Simplest *if* its box precision is adequate for masking and word-level
  granularity is available — both **unverified** (the coord-mapping issue + it is
  region/element-level, not obviously word-level).
- Risk: VLM coordinates may be too coarse for tight masking; no proven
  word-level geometry.

### C. PP-StructureV3 (geometry) + VLM (text) — *original sketch*

- PP-StructureV3 (layout + PP-OCRv5 + table) for structure + geometry; VL for
  text. PP-OCRv5 remains the recognition engine *inside* PP-StructureV3 (we are
  not dropping it).
- CPU-viable for the geometry layer. But inherits PaddleOCR's weak word boxes,
  which is the core redaction need — the main reason this slipped behind A.

## Cross-cutting decisions (hold regardless of A/B/C)

- **Keep the `Word` level.** It is the most precise ontology and redaction needs
  sub-line localization. Word boxes may be approximate (document the precision
  per chosen engine), but the contract keeps `Page → Block → Line → Word`.
- **Geometry is never owned by the VLM.** Whatever the geometry engine (docTR /
  PP-StructureV3), the VL only contributes text. If a VL box turns out usable, it
  is a bonus for alignment, not a dependency.
- **The runtime orchestrates and reconciles.** Inference services stay
  single-purpose model wrappers (ADR: runtime is the orchestrator). The runtime
  calls the geometry service and (optionally) the VL service and merges them.
- **VL is a separate, opt-in GPU service** (`nvisy-vl`), not bundled into the
  CPU OCR service — independent scaling/failure domains, customers opt out, the
  geometry OCR service stays CPU-viable. Matches the two-container philosophy.
- **Reconciliation is conservative** (research: *"VLMs Are Not (Yet) Spelling
  Correctors"*, arXiv 2509.17418): a Joint OCR–Correction policy, not blind
  replacement. Accept a VL text correction only when it is a **bounded edit**
  (low Levenshtein / ratio) of the geometry engine's text; keep the original
  otherwise. Prefer running VL only on **low-confidence** regions (cheaper, safer)
  — pending a usable confidence signal.
- **Contract/consistency fixes** (independent of engine choice): `OcrResponse`
  gains `modelId`; a shared `Probability` type moves to `nvisy-core`; constrain
  `polygon` to 4 points.

## Open questions the spike must answer

1. **PaddleOCR-VL 1.5 box precision + word granularity** — are the quad coords
   mask-tight after coordinate mapping? Region-level only, or word-level? (Gates
   option B and whether VL boxes help A's alignment.)
2. **docTR word-box accuracy** on our document types + its footprint/latency.
3. **Reconciliation feasibility** — can we reliably align VL text to the geometry
   engine's boxes (overlap if VL boxes usable; else reading-order + text
   similarity)?
4. **Confidence calibration** — is the geometry engine's per-region confidence a
   usable trigger for "verify this region with VL"?
5. **Footprint/GPU** — measured memory for each candidate; does the geometry
   service stay CPU-viable?

## Spike plan

Run each candidate on a representative sample (clean + messy + rotated +
multilingual) and measure:

- word/region box precision (IoU vs. ground truth; visual mask fit)
- text accuracy (edit distance)
- footprint + latency, CPU vs. GPU
- for A: can VL text be aligned to docTR boxes reliably?

Decide A vs. B vs. C from evidence, then write the committed design + rollout.

## Decision (pending spike)

Leaning **A (docTR + VLM)**: it is the only candidate that directly satisfies the
word-level-geometry requirement with a tool built for it, while getting VL text
accuracy — without betting masking precision on unverified VLM coordinates. B is
the simplicity prize *if* the spike shows VL boxes are mask-tight and
word-grained. C is the fallback if a CPU-only, no-VL deployment is needed.
