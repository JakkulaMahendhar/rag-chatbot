from app.core.ai_registry import AIServiceRegistry
from app.services.vector_store import VectorStoreService


class SearchService:

    def __init__(self):

        self.embedding_model = (
            AIServiceRegistry.get_embedding_model()
        )

    def search(
        self,
        query: str,
        top_k: int = 3
    ):

        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        )

        collection = VectorStoreService.get_collection()

        results = collection.query(
            query_embeddings=[
                query_embedding.tolist()
            ],
            n_results=top_k
        )

        formatted = []

        for i in range(
            len(results["ids"][0])
        ):

            formatted.append(

            {
                "chunk_id": results["ids"][0][i],

                "document": results["documents"][0][i], # type: ignore

                "metadata": results["metadatas"][0][i], # type: ignore

                "score": results["distances"][0][i] # type: ignore

            }

        )

        return formatted