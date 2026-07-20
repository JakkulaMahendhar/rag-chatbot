from app.core.ai_registry import AIServiceRegistry

from app.models.chunk import DocumentChunk
from app.models.embedding import DocumentEmbedding


class EmbeddingService:


    def __init__(self):

        self.model = AIServiceRegistry.get_embedding_model()



    def generate(
        self,
        chunks: list[DocumentChunk]
    ) -> list[DocumentEmbedding]:

        embeddings = []

        for chunk in chunks:

            vector = self.model.encode(
                chunk.content,
                convert_to_numpy=True
            )


            embeddings.append(

                DocumentEmbedding(

                    chunk_id=chunk.chunk_id,

                    document_id=chunk.document_id,

                    embedding=vector.tolist(),

                    metadata=chunk.metadata
                )

            )


        return embeddings



    def generate_query_embedding(
        self,
        text: str
    ) -> list[float]:


        vector = self.model.encode(

            text,

            convert_to_numpy=True

        )


        return vector.tolist()