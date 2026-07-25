from app.core.config import settings
from app.core.logger import logger
from app.services.hybrid_search import HybridSearchService


class RetrievalService:


    def __init__(self):

        logger.info(
            "Initializing Hybrid Retrieval Service"
        )

        self.hybrid_search = HybridSearchService()



    def retrieve(
        self,
        query_embedding: list[float],
        query: str
    ):


        logger.info(
            f"Retrieving top {settings.retrieval_top_k} hybrid results"
        )


        results = self.hybrid_search.search(

            query_embedding=query_embedding,

            query=query,

            top_k=settings.retrieval_top_k

        )


        return self._filter_by_score(results)



    def _filter_by_score(
        self,
        results
    ):


        logger.info(
            "Applying hybrid score filtering"
        )


        filtered = {

            "ids":[[]],

            "documents":[[]],

            "metadatas":[[]],

            "distances":[[]]

        }


        total = len(results["ids"][0])


        for index, score in enumerate(results["distances"][0]):


            if score >= settings.hybrid_similarity_threshold:


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
                    score
                )


        logger.info(

            f"""
Hybrid filtering completed

Retrieved:
{total}

Accepted:
{len(filtered['ids'][0])}

Rejected:
{total - len(filtered['ids'][0])}

Threshold:
{settings.hybrid_similarity_threshold}
"""

        )


        return filtered