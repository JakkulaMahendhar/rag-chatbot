from pathlib import Path

import chromadb

from app.core.logger import logger
from app.models.chunk import DocumentChunk
from app.models.embedding import DocumentEmbedding
from app.core.config import settings

class VectorStoreService:

    def __init__(self):

        db_path = Path(settings.chroma_path)

        db_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.client = chromadb.PersistentClient(
            path=str(db_path)
        )

        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[DocumentEmbedding]
    ):

        self.collection.add(
            ids=[str(chunk.chunk_id) for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=[embedding.embedding for embedding in embeddings],
            metadatas=[chunk.metadata for chunk in chunks]
        )

        logger.info(
            f"Stored {len(chunks)} vectors in ChromaDB"
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3
    ):

        logger.info(
            f"Vector search started | top_k={top_k}"
        )

        try:

            results = self.collection.query(

                query_embeddings=[
                    query_embedding
                ],

                n_results=top_k

            )


            documents = results.get(
                "documents",
                [[]]
            )[0] # type: ignore


            metadatas = results.get(
                "metadatas",
                [[]]
            )[0] # type: ignore


            distances = results.get(
                "distances",
                [[]]
            )[0] # type: ignore


            logger.info(
                f"Vector search completed | "
                f"chunks={len(documents)}"
            )


            for index, document in enumerate(documents):

                metadata = (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                )


                distance = (
                    distances[index]
                    if index < len(distances)
                    else None
                )


                logger.debug(
                    f"""
                Retrieved chunk:
                index={index}
                filename={metadata.get('filename')}
                distance={distance}
                content={document[:100]}
                """
                )


            return results


        except Exception as e:


            logger.exception(
            "Vector search failed"
            )

            raise e

    def stats(self):

        return {
            "collection": self.collection.name,
            "vectors": self.collection.count()
        }