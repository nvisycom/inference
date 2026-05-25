"""NER inference service (GLiNER) exposed over HTTP via BentoML.

The default implementation of the NER wire contract (``nvisy_core.ner.v1``).
Scaffold stub — GLiNER wiring is filled in by a follow-up.

Run locally::

    uv run bentoml serve nvisy_gliner.service:NerService --reload
"""

from __future__ import annotations

import bentoml
from nvisy_core.ner.v1 import NerRequest, NerResponse

from nvisy_gliner.label_map import DEFAULT_LABEL_MAP, LabelMap


@bentoml.service(
    name="nvisy-inference-gliner",
    resources={"cpu": "2"},
    traffic={"timeout": 60},
)
class NerService:
    def __init__(self) -> None:
        # Owns the translation between the canonical EntityKind taxonomy and
        # GLiNER's free-text labels — see nvisy_gliner.label_map.
        self.label_map: LabelMap = DEFAULT_LABEL_MAP
        # TODO(follow-up): load GLiNER here.
        #   from gliner import GLiNER
        #   self.model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        self.model = None

    @bentoml.api(batchable=True, max_batch_size=16, max_latency_ms=80)
    async def recognize(self, requests: list[NerRequest]) -> list[NerResponse]:
        # Per request, the flow will be:
        #   labels = self.label_map.labels_for(req.kinds)
        #   spans  = self.model.predict_entities(req.text, labels, req.threshold)
        #   entities = [Entity(text=s["text"], kind=k, score=s["score"],
        #                      start=s["start"], end=s["end"])
        #               for s in spans
        #               if (k := self.label_map.classify(s["label"])) is not None]
        raise NotImplementedError("NER inference not wired yet (scaffold stub).")
