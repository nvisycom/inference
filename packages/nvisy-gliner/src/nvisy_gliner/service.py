"""NER inference service (GLiNER) exposed over HTTP via BentoML.

The default implementation of the NER wire contract (``nvisy_core.ner.v1``).
Scaffold stub — GLiNER wiring is filled in by a follow-up.

Run locally::

    uv run bentoml serve nvisy_gliner.service:NerService --reload
"""

from __future__ import annotations

import bentoml
from nvisy_core.ner.v1 import NerRequest, NerResponse


@bentoml.service(
    name="nvisy-inference-gliner",
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
