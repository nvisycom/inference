"""Generate the inference services' OpenAPI specs into ``docs/openapi/``.

BentoML builds an OpenAPI document per service (the same one served at
``/docs.json``). We extract it as-is — it reflects the real endpoints and the
``nvisy-core`` v1 types BentoML inlines, so it can't drift from what the
services actually serve. The committed JSON is the machine-readable wire
contract for bring-your-own-inference (BYOI) implementers.

Run::

    uv run python scripts/gen_openapi.py          # write specs
    uv run python scripts/gen_openapi.py --check   # fail if out of date (CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nvisy_doctr.service import OcrService
from nvisy_gliner.service import NerService

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "openapi"
SERVICES = {"ocr": OcrService, "ner": NerService}


def render(service: object) -> str:
    spec = service.openapi_spec.asdict()
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any committed spec differs from the generated one.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for name, service in SERVICES.items():
        path = OUT_DIR / f"{name}.json"
        generated = render(service)
        if args.check:
            current = path.read_text() if path.exists() else ""
            if current != generated:
                stale.append(name)
        else:
            path.write_text(generated)
            print(f"wrote {path.relative_to(OUT_DIR.parent.parent)}")

    if args.check and stale:
        print(
            f"OpenAPI specs out of date: {', '.join(stale)}. "
            "Run `uv run python scripts/gen_openapi.py`.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
