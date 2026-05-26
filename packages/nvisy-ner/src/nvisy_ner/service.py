"""NER inference service (GLiNER) exposed over HTTP via BentoML.

The default implementation of the NER wire contract (``nvisy_core.ner.v1``).

Run locally::

    uv run bentoml serve nvisy_ner.service:NerService --reload
"""

from __future__ import annotations

import bentoml
from bentoml.exceptions import InternalServerError
from nvisy_core.entity import EntityKind
from nvisy_core.ner.v1 import Entity, NerRequest, NerResponse
from nvisy_core.runtime import get_logger, request_id, resolve_model
from prometheus_client import Histogram

from nvisy_ner.label_map import DEFAULT_LABEL_MAP, LabelMap

logger = get_logger("nvisy.ner")

# Built-in default model id. Declared as the NVISY_MODEL_NAME env default below,
# so it is the single source of truth and shows up in the bento manifest.
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
    "packages/nvisy-ner/requirements.txt"
)


@bentoml.service(
    name="nvisy-inference-ner",
    image=image,
    resources={"cpu": "2"},
    traffic={"timeout": 60},
    # Declared with defaults so they're optional + documented in the bento
    # manifest. NVISY_MODEL_PATH defaults to the /models mount (empty unless BYO
    # weights are mounted); NVISY_MODEL_NAME is the model loaded otherwise.
    envs=[
        {"name": "NVISY_MODEL_PATH", "value": "/models"},
        {"name": "NVISY_MODEL_NAME", "value": DEFAULT_MODEL},
    ],
)
class NerService:
    def __init__(self) -> None:
        from gliner import GLiNER

        # Owns the translation between the canonical EntityKind taxonomy and
        # GLiNER's free-text labels — see nvisy_ner.label_map.
        self.label_map: LabelMap = DEFAULT_LABEL_MAP
        self.model_id = resolve_model()
        logger.info("loading GLiNER (model=%s)", self.model_id)
        self.model = GLiNER.from_pretrained(self.model_id)
        logger.info("GLiNER ready")

    # Sync (not async): inference is CPU/GPU-bound and blocking. BentoML runs
    # sync endpoints in a managed thread pool, so this never blocks the event
    # loop (an async def here would, and could starve /readyz).
    @bentoml.api(batchable=True, max_batch_size=16, max_latency_ms=80)
    def recognize(
        self,
        requests: list[NerRequest],
        ctx: bentoml.Context,
    ) -> list[NerResponse]:
        batch_size_metric.observe(len(requests))
        rid = request_id(ctx)
        logger.info("recognize batch=%d req_id=%s", len(requests), rid)
        try:
            return [self._recognize_one(req) for req in requests]
        except Exception as exc:
            # Surface inference failures as a clean 500 rather than a raw stack
            # trace; the error is visible, not silently swallowed.
            logger.exception("inference failed (req_id=%s)", rid)
            raise InternalServerError("NER inference failed") from exc

    def _recognize_one(self, req: NerRequest) -> NerResponse:
        labels = self.label_map.labels_for(req.kinds)
        if not labels:
            # None of the requested kinds map to a model label (e.g. all
            # visual/biometric); nothing for a text model to find.
            return NerResponse(entities=[], model_id=self.model_id)
        spans = self.model.predict_entities(
            req.text,
            labels,
            threshold=req.threshold,
            return_class_probs=req.return_class_probs,
        )
        entities: list[Entity] = []
        for span in spans:
            # We only request mapped labels, so classify() normally succeeds;
            # guard anyway in case the model echoes an unexpected label.
            kind = self.label_map.classify(span["label"])
            if kind is None:
                continue
            entities.append(
                Entity(
                    text=span["text"],
                    kind=kind,
                    score=float(span["score"]),
                    start=int(span["start"]),
                    end=int(span["end"]),
                    class_probs=self._map_class_probs(span.get("class_probs")),
                )
            )
        return NerResponse(entities=entities, model_id=self.model_id)

    def _map_class_probs(self, probs: object) -> dict[EntityKind, float] | None:
        """Map GLiNER's label->prob dict onto EntityKind, dropping unmapped labels."""
        if not isinstance(probs, dict):
            return None
        mapped: dict[EntityKind, float] = {}
        for label, prob in probs.items():
            kind = self.label_map.classify(label)
            if kind is not None:
                mapped[kind] = float(prob)
        return mapped or None
