from app.core.logger import logger


class VectorStoreService:


    def __init__(self):

        self.collection = (
            self.get_collection() # pyright: ignore[reportAttributeAccessIssue]
        )


    def search(
        self,
        query_embedding: list[float],
        top_k: int
    ):

        try:

            results = self.collection.query(

                query_embeddings=[
                    query_embedding
                ],

                n_results=top_k

            )


            return results


        except Exception as e:

            logger.exception(
                "Vector search failed"
            )

            raise e