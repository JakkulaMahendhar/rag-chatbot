from pathlib import Path

import chromadb

from app.core.config import settings
from app.core.logger import logger
from app.models.chunk import DocumentChunk
from app.models.embedding import DocumentEmbedding


class VectorStoreService:

    def __init__(self):

        db_path = Path(settings.chroma_path)

        db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(db_path))

        self.collection = self.client.get_or_create_collection(name="documents")

        logger.info(
            f"ChromaDB initialized | "
            f"Path={db_path} | "
            f"Collection={self.collection.name} | "
            f"Vectors={self.collection.count()}"
        )

        logger.info(f"Chroma collection metadata | " f"{self.collection.metadata}")

        logger.info(
            f"Chroma collection configuration | " f"{self.collection.configuration}"
        )

    # ==========================================================
    # ADD CHUNKS
    # ==========================================================

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[DocumentEmbedding],
    ):

        self.collection.upsert(
            ids=[str(chunk.chunk_id) for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=[embedding.embedding for embedding in embeddings],
            metadatas=[chunk.metadata for chunk in chunks],
        )

        logger.info(f"Stored {len(chunks)} vectors in ChromaDB")

    # ==========================================================
    # VECTOR SEARCH
    # ==========================================================

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        document_ids: list[str] | None = None,
    ):

        logger.info(
            f"Vector search started | "
            f"top_k={top_k} | "
            f"document_ids={document_ids}"
        )

        try:

            # --------------------------------------------------
            # TEMPORARY DEBUG
            #
            # This shows exactly what is stored in ChromaDB
            # before executing the query.
            # --------------------------------------------------

            # self.debug_all_chunks()

            # --------------------------------------------------
            # Build Chroma filter
            # --------------------------------------------------

            where = None

            if document_ids:

                document_ids = [str(document_id) for document_id in document_ids]

                if len(document_ids) == 1:

                    where = {"document_id": document_ids[0]}

                else:

                    where = {
                        "$or": [
                            {"document_id": document_id} for document_id in document_ids
                        ]
                    }

                logger.info(
                    f"Applying Chroma document filter | " f"document_ids={document_ids}"
                )

            # --------------------------------------------------
            # Execute vector search
            # --------------------------------------------------

            if where:

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where,
                )

            else:

                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
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

Document ID:
{item["metadata"].get("document_id")}

Distance:
{distances[i]}

Filename:
{item["metadata"].get("filename")}
""")

            logger.info(f"Vector search completed | " f"chunks={len(vector_results)}")

            return vector_results

        except Exception:

            logger.exception("Vector search failed")

            raise

    # ==========================================================
    # STATS
    # ==========================================================

    def stats(self):

        return {
            "collection": self.collection.name,
            "vectors": self.collection.count(),
        }

    # ==========================================================
    # DELETE DOCUMENT
    # ==========================================================

    def delete_document(
        self,
        document_id: str,
    ):
        """
        Remove all embeddings related
        to a document from ChromaDB.
        """

        document_id = str(document_id)

        logger.info(f"Deleting Chroma vectors | " f"document_id={document_id}")

        self.collection.delete(where={"document_id": document_id})

        logger.info(f"Chroma vectors deleted | " f"document_id={document_id}")

    # ==========================================================
    # DEBUG ALL CHUNKS
    # ==========================================================

    def debug_all_chunks(self):

        try:

            result = self.collection.get(
                include=[
                    "documents",
                    "metadatas",
                ]
            )

            ids = result.get("ids", [])

            documents = result.get("documents", [])

            metadatas = result.get("metadatas", [])

            logger.info(
                "\n" "========== CHROMA DEBUG ==========\n" f"Total chunks: {len(ids)}"
            )

            for index, chunk_id in enumerate(ids):

                metadata = metadatas[index] if index < len(metadatas) else {}

                content = documents[index] if index < len(documents) else ""

                logger.info(f"""
------------------------------
Chunk #{index + 1}

Chunk ID:
{chunk_id}

Document ID:
{metadata.get("document_id")}

Filename:
{metadata.get("filename")}

Metadata:
{metadata}

Content:
{content[:200]}
------------------------------
""")

            logger.info("========== END CHROMA DEBUG ==========")

            return result

        except Exception:

            logger.exception("Failed to debug ChromaDB chunks")

            raise
