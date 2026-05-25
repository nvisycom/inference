"""NER inference service (GLiNER) exposed over HTTP via BentoML.

The default implementation of the NER wire contract (``nvisy_core.ner.v1``).

Run locally::

    uv run bentoml serve nvisy_gliner.service:NerService --reload
"""

from __future__ import annotations

import bentoml
from bentoml.exceptions import ServiceUnavailable
from nvisy_core.ner.v1 import Entity, NerRequest, NerResponse
from nvisy_core.runtime import get_logger, request_id, resolve_model
from prometheus_client import Histogram

from nvisy_gliner.label_map import DEFAULT_LABEL_MAP, LabelMap

logger = get_logger("nvisy.gliner")

# Default model id (NVISY_MODEL_NAME overrides; NVISY_MODEL_PATH / /models mount
# overrides with on-disk weights). See nvisy_core.runtime.resolve_model.
DEFAULT_MODEL = "urchade/gliner_multi-v2.1"

# prometheus_client directly (bentoml.metrics is deprecated in 1.4); BentoML
# sets PROMETHEUS_MULTIPROC_DIR so this is multiprocess-safe across workers.
batch_size_metric = Histogram(
    "nvisy_ner_batch_size",
    "Number of texts merged into one recognize() call.",
    buckets=(1, 2, 4, 8, 16, 32),
)

# BentoML builds the image from this config (`bentoml build` + `containerize`);
# no hand-written Dockerfile. The requirements file is exported per-service from
# the workspace lock (scripts/gen_requirements.py); bundled source is scoped by
# bentofile.yaml's `include`. lock_python_packages=False: the file is already
# locked + hashed, so BentoML must not re-resolve it.
image = bentoml.images.Image(python_version="3.12", lock_python_packages=False).requirements_file(
    "packages/nvisy-gliner/requirements.txt"
)


@bentoml.service(
    name="nvisy-inference-gliner",
    image=image,
    resources={"cpu": "2"},
    traffic={"timeout": 60},
    envs=[{"name": "NVISY_MODEL_PATH"}, {"name": "NVISY_MODEL_NAME"}, {"name": "LOG_LEVEL"}],
)
class NerService:
    def __init__(self) -> None:
        from gliner import GLiNER

        # Owns the translation between the canonical EntityKind taxonomy and
        # GLiNER's free-text labels — see nvisy_gliner.label_map.
        self.label_map: LabelMap = DEFAULT_LABEL_MAP
        model = resolve_model(DEFAULT_MODEL)
        logger.info("loading GLiNER (model=%s)", model)
        self.model = GLiNER.from_pretrained(model)
        logger.info("GLiNER ready")

    @bentoml.api(batchable=True, max_batch_size=16, max_latency_ms=80)
    async def recognize(
        self,
        requests: list[NerRequest],
        ctx: bentoml.Context,
    ) -> list[NerResponse]:
        if self.model is None:  # pragma: no cover - defensive; __init__ loads eagerly
            raise ServiceUnavailable("NER model is not loaded")
        batch_size_metric.observe(len(requests))
        logger.info("recognize batch=%d req_id=%s", len(requests), request_id(ctx))
        return [self._recognize_one(req) for req in requests]

    def _recognize_one(self, req: NerRequest) -> NerResponse:
        labels = self.label_map.labels_for(req.kinds)
        if not labels:
            # None of the requested kinds map to a model label.
            return NerResponse(entities=[])
        spans = self.model.predict_entities(req.text, labels, threshold=req.threshold)
        entities: list[Entity] = []
        for span in spans:
            kind = self.label_map.classify(span["label"])
            if kind is None:  # label not in our taxonomy — drop it
                continue
            entities.append(
                Entity(
                    text=span["text"],
                    kind=kind,
                    score=float(span["score"]),
                    start=int(span["start"]),
                    end=int(span["end"]),
                )
            )
        return NerResponse(entities=entities)
