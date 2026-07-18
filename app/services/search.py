from app.core.ai_registry import AIServiceRegistry
from app.services.retrieval import RetrievalService


class SearchService:


    def __init__(self):

        self.embedding_model = (
            AIServiceRegistry
            .get_embedding_model()
        )

        self.retrieval_service = (
            RetrievalService()
        )


    def search(
        self,
        query: str,
        top_k: int = 3
    ):


        query_embedding = (
            self.embedding_model.encode(
                query,
                convert_to_numpy=True
            )
        )


        results = (
            self.retrieval_service.retrieve(
                query_embedding.tolist(),
                top_k
            )
        )


        return self.format_results(results)



    def format_results(
        self,
        results
    ):

        formatted = []


        for index in range(
            len(results["ids"][0])
        ):

            formatted.append(

                {

                    "chunk_id":
                    results["ids"][0][index],


                    "document":
                    results["documents"][0][index],


                    "metadata":
                    results["metadatas"][0][index],


                    "score":
                    results["distances"][0][index]

                }

            )


        return formatted