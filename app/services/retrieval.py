from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.database.repositories.document_repository import DocumentRepository
from app.services.hybrid_search import HybridSearchService


class RetrievalService:

    def __init__(self, session: AsyncSession):

        logger.info("Initializing Retrieval Service")

        self.hybrid_search = HybridSearchService()

        # PostgreSQL repository.
        # Responsible for resolving document ownership.
        self.document_repository = DocumentRepository(session)

    # ============================================================
    # MULTI QUERY RETRIEVAL
    # ============================================================

    async def multi_retrieve(
        self,
        queries: list[str],
        embedding_service,
        user_id: int | None = None,
    ):
        """
        Execute multiple expanded queries for one user.

        Flow:

        user_id
            ↓
        PostgreSQL
            ↓
        document_ids
            ↓
        retrieve()
            ↓
        Hybrid Search
            ↓
        merge + deduplicate
        """

        logger.info(
            f"Multi query retrieval started | "
            f"User={user_id} | Queries={len(queries)}"
        )

        # --------------------------------------------------------
        # Resolve user's documents ONCE.
        # --------------------------------------------------------

        document_ids = await self.document_repository.get_user_document_ids(user_id)

        document_ids = [str(document_id) for document_id in document_ids]

        logger.info(
            f"User documents resolved | "
            f"User={user_id} | "
            f"Documents={len(document_ids)}"
        )

        if not document_ids:

            logger.info(f"No documents available for user | User={user_id}")

            return []

        merged_results = []

        # --------------------------------------------------------
        # Execute every expanded query.
        # --------------------------------------------------------

        for query in queries:

            logger.info(
                f"Executing retrieval query | " f"User={user_id} | Query={query}"
            )

            query_embedding = embedding_service.generate_query_embedding(query)

            results = await self.retrieve(
                query_embedding=query_embedding,
                query=query,
                document_ids=document_ids,
            )

            documents = self._convert_to_documents(results)

            merged_results.extend(documents)

        logger.info(
            f"Multi query retrieval completed | "
            f"User={user_id} | "
            f"Documents={len(merged_results)}"
        )

        return self._remove_duplicates(merged_results)

    # ============================================================
    # USER-SCOPED SINGLE QUERY RETRIEVAL
    # ============================================================

    async def retrieve_for_user(
        self,
        query_embedding: list[float],
        query: str,
        user_id: int,
    ):
        """
        Resolve the user's document IDs and execute retrieval.

        Used by endpoints such as /search where only user_id
        is available.
        """

        logger.info(f"User-scoped retrieval started | User={user_id}")

        document_ids = await self.document_repository.get_user_document_ids(user_id)

        logger.info(
            f"User documents resolved | "
            f"User={user_id} | "
            f"Documents={len(document_ids)}"
        )

        if not document_ids:

            logger.info(f"No documents available for user | User={user_id}")

            return self._empty_results()

        return await self.retrieve(
            query_embedding=query_embedding,
            query=query,
            document_ids=document_ids,
        )

    # ============================================================
    # LOW-LEVEL RETRIEVAL
    # ============================================================

    async def retrieve(
        self,
        query_embedding: list[float],
        query: str,
        document_ids: list[str],
    ):
        """
        Execute hybrid retrieval against a known set of
        user-owned document IDs.

        IMPORTANT:

        This method does NOT know about user_id.

        Ownership has already been resolved before calling it.
        """

        logger.info(
            f"Retrieving top {settings.retrieval_top_k} hybrid results | "
            f"Documents={len(document_ids)}"
        )

        results = self.hybrid_search.search(
            query_embedding=query_embedding,
            query=query,
            top_k=settings.retrieval_top_k,
            document_ids=document_ids,
        )

        return self._filter_by_score(results)

    # ============================================================
    # CONVERT RESULTS
    # ============================================================

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

    # ============================================================
    # REMOVE DUPLICATES
    # ============================================================

    def _remove_duplicates(self, documents):

        unique = {}

        for document in documents:

            unique[document["id"]] = document

        return list(unique.values())

    # ============================================================
    # SCORE FILTER
    # ============================================================

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

        accepted = len(filtered["ids"][0])
        rejected = total - accepted

        logger.info(
            f"Hybrid filtering completed | "
            f"Retrieved={total} | "
            f"Accepted={accepted} | "
            f"Rejected={rejected} | "
            f"Threshold={settings.hybrid_score_threshold}"
        )

        return filtered

    # ============================================================
    # EMPTY RESULT
    # ============================================================

    def _empty_results(self):

        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "hybrid_scores": [[]],
        }
