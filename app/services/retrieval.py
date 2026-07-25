from app.core.config import settings
from app.core.logger import logger
from app.services.vector_store import VectorStoreService
from chromadb.api.types import QueryResult


class RetrievalService:

    def __init__(self):

        self.vector_store = VectorStoreService()

    def retrieve(
        self,
        query_embedding: list[float]
    ):

        logger.info(
            f"Retrieving top {settings.retrieval_top_k} similar chunks"
        )

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=settings.retrieval_top_k
        )

        logger.info(
            f"Raw distances from Chroma: {results['distances']}"
        )

        return self._filter_by_distance(results)

    def _filter_by_distance(
        self,
        results: dict
    ) -> dict:

        logger.info(
            "Applying distance threshold filtering"
        )

        if not results.get("ids") or not results["ids"]:

            logger.warning(
                "Vector search returned no results."
            )

            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        filtered = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

        total = len(results["ids"][0])

        for index, distance in enumerate(results["distances"][0]):

            logger.debug(
                f"Chunk {index + 1} | Distance={distance:.4f}"
            )

            if distance <= settings.distance_threshold:

                logger.debug(
                    f"Chunk {index + 1} accepted"
                )

                filtered["ids"][0].append(
                    results["ids"][0][index]
                )

                filtered["documents"][0].append(
                    results["documents"][0][index]
                )

                filtered["metadatas"][0].append(
                    results["metadatas"][0][index]
                )

                filtered["distances"][0].append(
                    distance
                )

            else:

                logger.debug(
                    f"Chunk {index + 1} rejected"
                )

        logger.info(
            f"Retrieved={total} | "
            f"Accepted={len(filtered['ids'][0])} | "
            f"Rejected={total - len(filtered['ids'][0])} | "
            f"Threshold={settings.distance_threshold}"
        )

        return filtered