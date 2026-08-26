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

        logger.info("Cross Encoder reranking completed")

        return ranked[:3]
