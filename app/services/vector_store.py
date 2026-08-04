from pathlib import Path

import chromadb

from app.core.logger import logger
from app.models.chunk import DocumentChunk
from app.models.embedding import DocumentEmbedding
from app.core.config import settings


class VectorStoreService:

    def __init__(self):

        db_path = Path(settings.chroma_path)

        db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(db_path))

        self.collection = self.client.get_or_create_collection(name="documents")

    def add_chunks(
        self, chunks: list[DocumentChunk], embeddings: list[DocumentEmbedding]
    ):

        self.collection.upsert(
            ids=[str(chunk.chunk_id) for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=[embedding.embedding for embedding in embeddings],
            metadatas=[chunk.metadata for chunk in chunks],
        )

        logger.info(f"Stored {len(chunks)} vectors in ChromaDB")

    def search(self, query_embedding: list[float], top_k: int = 3):

        logger.info(f"Vector search started | top_k={top_k}")

        try:

            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=top_k
            )

            ids = results.get("ids", [[]])[0]

            documents = results.get("documents", [[]])[0]

            metadatas = results.get("metadatas", [[]])[0]

            distances = results.get("distances", [[]])[0]

            vector_results = []

            for i in range(len(ids)):

                item = {
                    "id": ids[i],
                    "document": documents[i],
                    "distance": distances[i],
                    "metadata": (metadatas[i] if i < len(metadatas) else {}),
                }

                vector_results.append(item)

                logger.debug(f"""
                Vector Result

                ID:
                {ids[i]}

                Distance:
                {distances[i]}

                Filename:
                {item['metadata'].get('filename')}
                """)

            logger.info(f"Vector search completed | chunks={len(vector_results)}")

            return vector_results

        except Exception:

            logger.exception("Vector search failed")

        raise

    def stats(self):

        return {"collection": self.collection.name, "vectors": self.collection.count()}

    def delete_document(self, document_id: str):
        """
        Remove all embeddings related
        to a document from ChromaDB.
        """

        self.collection.delete(where={"document_id": document_id})
