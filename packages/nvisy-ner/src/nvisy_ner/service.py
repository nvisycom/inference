"""NER inference service (GLiNER) exposed over HTTP via BentoML.

Scaffold stub — GLiNER wiring is filled in by a follow-up. Request/response
types come from ``nvisy_core.ner`` (the shared wire contract).

Run locally::

    uv run bentoml serve nvisy_ner.service:NerService --reload
"""

from __future__ import annotations

import bentoml
from nvisy_core.ner import NerRequest, NerResponse


@bentoml.service(
    name="nvisy-inference-ner",
    resources={"cpu": "2"},
    traffic={"timeout": 60},
)
class NerService:
    def __init__(self) -> None:
        # TODO(follow-up): load GLiNER here.
        #   from gliner import GLiNER
        #   self.model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        self.model = None

    @bentoml.api(batchable=True, max_batch_size=16, max_latency_ms=80)
    async def recognize(self, requests: list[NerRequest]) -> list[NerResponse]:
        raise NotImplementedError("NER inference not wired yet (scaffold stub).")
