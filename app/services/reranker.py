from app.core.config import settings
from app.core.logger import logger
import math


class Reranker:

    def __init__(self):

        # Deferred import - see app/core/ai_registry.py for why.
        from sentence_transformers import CrossEncoder

        logger.info("Initializing Cross Encoder Reranker")

        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        logger.info("Cross Encoder loaded")

    def rerank(self, query: str, documents: list):

        if not documents:
            return []

        logger.info(f"Cross Encoder reranking started | Documents={len(documents)}")

        pairs = [[query, doc.content] for doc in documents]

        scores = self.model.predict(pairs)

        for doc, score in zip(documents, scores):

            doc.rerank_score = 1 / (1 + math.exp(-float(score)))

        ranked = sorted(documents, key=lambda x: x.rerank_score, reverse=True)

        # settings.reranker_score_threshold existed but was never actually
        # applied here - rerank() always returned exactly the top 3,
        # however weak, which meant a genuinely unrelated chunk (e.g. from
        # a completely different uploaded document) could still fill a
        # slot just to hit the count, get fed into the LLM's context, and
        # show up in the sources list at ~0% relevance. Dropping anything
        # below the threshold first means "nothing relevant enough" can
        # correctly mean fewer than 3 sources, or zero - which the
        # existing "I don't have enough information" prompt rule already
        # handles for an empty context.
        ranked = [
            document
            for document in ranked
            if document.rerank_score >= settings.reranker_score_threshold
        ]

        logger.info(
            f"Cross Encoder reranking completed | "
            f"Above threshold ({settings.reranker_score_threshold})={len(ranked)}"
        )

        return ranked[:3]
