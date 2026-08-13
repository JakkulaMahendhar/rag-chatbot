from app.core.ai_registry import AIServiceRegistry
from app.services.retrieval import RetrievalService


class SearchService:

    def __init__(self, session):

        self.embedding_model = AIServiceRegistry.get_embedding_model()

        self.retrieval_service = RetrievalService(session=session)

    async def search(
        self,
        query: str,
        top_k: int = 3,
        user_id: int | None = None,
    ):

        if user_id is None:
            raise ValueError("user_id is required")

        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
        )

        results = await self.retrieval_service.retrieve_for_user(
            query_embedding=query_embedding.tolist(),
            query=query,
            user_id=user_id,
        )

        return self.format_results(results)

    def format_results(self, results):

        formatted = []

        for index in range(len(results["ids"][0])):

            formatted.append(
                {
                    "chunk_id": results["ids"][0][index],
                    "document": results["documents"][0][index],
                    "metadata": results["metadatas"][0][index],
                    "score": results["distances"][0][index],
                }
            )

        return formatted
