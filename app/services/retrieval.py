from app.core.config import settings
from app.core.logger import logger
from app.services.hybrid_search import HybridSearchService


class RetrievalService:

    def __init__(self):

        logger.info("Initializing Hybrid Retrieval Service")

        self.hybrid_search = HybridSearchService()

    def multi_retrieve(self, queries: list[str], embedding_service):
        """
        Executes multiple expanded queries
        and merges hybrid retrieval results
        """

        logger.info(f"""
Multi query retrieval started

Queries:
{queries}

Total:
{len(queries)}

""")

        merged_results = []

        for query in queries:

            logger.info(f"""
Executing retrieval query

{query}

""")

            # Generate embedding
            query_embedding = embedding_service.generate_query_embedding(query)

            results = self.retrieve(query_embedding=query_embedding, query=query)

            documents = self._convert_to_documents(results)

            merged_results.extend(documents)

        logger.info(f"""
Multi query retrieval completed

Documents:
{len(merged_results)}

""")

        return self._remove_duplicates(merged_results)

    def retrieve(self, query_embedding: list[float], query: str):

        logger.info(f"Retrieving top {settings.retrieval_top_k} hybrid results")

        results = self.hybrid_search.search(
            query_embedding=query_embedding, query=query, top_k=settings.retrieval_top_k
        )

        return self._filter_by_score(results)

    def _convert_to_documents(self, results):

        documents = []

        for index, content in enumerate(results["documents"][0]):

            documents.append(
                {
                    "id": results["ids"][0][index],
                    "content": content,
                    "metadata": results["metadatas"][0][index],
                    "score": results["distances"][0][index],
                }
            )

        return documents

    def _remove_duplicates(self, documents):

        unique = {}

        for doc in documents:

            unique[doc["id"]] = doc

        return list(unique.values())

    def _filter_by_score(self, results):

        logger.info("Applying hybrid score filtering")

        filtered = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "hybrid_scores": [[]],
        }

        total = len(results["ids"][0])

        for index, score in enumerate(results["hybrid_scores"][0]):

            if score >= settings.hybrid_score_threshold:

                filtered["ids"][0].append(results["ids"][0][index])

                filtered["documents"][0].append(results["documents"][0][index])

                filtered["metadatas"][0].append(results["metadatas"][0][index])

                filtered["distances"][0].append(score)

                filtered["hybrid_scores"][0].append(score)

        logger.info(f"""
Hybrid filtering completed

Retrieved:
{total}

Accepted:
{len(filtered['ids'][0])}

Rejected:
{total - len(filtered['ids'][0])}

Threshold:
{settings.hybrid_score_threshold}

""")

        return filtered
