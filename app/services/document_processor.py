from pathlib import Path

from app.core.exceptions import DocumentProcessingException
from app.core.logger import logger

from app.services.chunk_storage import ChunkStorageService
from app.services.embedding_storage import EmbeddingStorageService
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

from app.models.bm25_document import BM25Document

from app.database.models.document import Document


class DocumentProcessingService:
    """
    Slow phase of document upload: parse, chunk, embed, and index
    an already-saved document. Run by the worker (app/worker.py),
    not the web request - see DocumentRegistrationService for the
    fast phase that runs inline in the request.
    """

    def __init__(
        self,
        parser_service,
        chunking_service,
        embedding_service,
        document_repository,
    ):
        self.parser_service = parser_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.document_repository = document_repository

    async def process_document(self, document: Document) -> dict:

        try:

            document.status = "processing"

            await self.document_repository.save(document)

            location = Path(document.file_path)

            # -----------------------------------
            # Parse Document
            # -----------------------------------

            text = self.parser_service.parse(location)

            # -----------------------------------
            # PostgreSQL Document ID
            #
            # This is the SINGLE document ID
            # used throughout the retrieval pipeline.
            # -----------------------------------

            database_document_id = str(document.id)

            logger.info(
                f"Processing document | "
                f"document_id={database_document_id} | "
                f"user_id={document.user_id}"
            )

            # -----------------------------------
            # Generate Chunks
            # -----------------------------------

            chunks = self.chunking_service.split(
                text=text,
                document_id=database_document_id,
                metadata={
                    "document_id": database_document_id,
                    "user_id": str(document.user_id),
                    "filename": location.name,
                    "type": location.suffix,
                },
            )

            logger.info(f"Generated chunks: {len(chunks)}")

            # -----------------------------------
            # Save Chunks
            # -----------------------------------

            ChunkStorageService.save(
                document_id=database_document_id,
                chunks=chunks,
            )

            # -----------------------------------
            # Generate Embeddings
            # -----------------------------------

            embeddings = self.embedding_service.generate(chunks)

            # -----------------------------------
            # Save Embeddings
            # -----------------------------------

            EmbeddingStorageService.save(
                document_id=database_document_id,
                embeddings=embeddings,
            )

            # -----------------------------------
            # Store Chroma Vectors
            # -----------------------------------

            vector_store = VectorStoreService()

            vector_store.add_chunks(
                chunks=chunks,
                embeddings=embeddings,
            )

            logger.info("Document stored successfully in vector database")

            # -----------------------------------
            # Store BM25
            # -----------------------------------

            bm25_service = BM25SearchService()

            bm25_documents = []

            for chunk in chunks:

                bm25_documents.append(
                    BM25Document(
                        chunk_id=str(chunk.chunk_id),
                        document_id=str(chunk.metadata["document_id"]),
                        content=chunk.content,
                        metadata=chunk.metadata,
                    )
                )

            bm25_service.add_documents(bm25_documents)

            logger.info("Document stored successfully in BM25 index")

            document.status = "completed"

            await self.document_repository.save(document)

            return {
                "document_id": database_document_id,
                "filename": location.name,
                "size": location.stat().st_size,
                "extracted_characters": len(text),
                "total_chunks": len(chunks),
                "total_embeddings": len(embeddings),
            }

        except Exception as e:

            logger.exception("Document processing failed")

            document.status = "failed"
            document.error_message = str(e)[:2000]

            await self.document_repository.save(document)

            raise DocumentProcessingException("Unable to process document.") from e
