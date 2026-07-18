from app.services.vector_store import VectorStoreService
from app.core.logger import logger


class RetrievalService:

    def __init__(self):

        self.vector_store = VectorStoreService()


    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = 3
    ):

        logger.info(
            f"Retrieving top {top_k} similar chunks"
        )


        results = self.vector_store.search( # pyright: ignore[reportAttributeAccessIssue]
            query_embedding=query_embedding,
            top_k=top_k
        )


        return results