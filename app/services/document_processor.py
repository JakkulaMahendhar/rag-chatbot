from fastapi import UploadFile

from app.core.exceptions import DocumentProcessingException
from app.core.logger import logger

from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.chunk_storage import ChunkStorageService
from app.services.embedding import EmbeddingService
from app.services.embedding_storage import EmbeddingStorageService
from app.services.vector_store import VectorStoreService
from app.services.bm25_search import BM25SearchService

from app.models.bm25_document import BM25Document

from app.database.models.document import Document


class DocumentProcessingService:

    def __init__(
        self,
        storage_service,
        parser_service,
        chunking_service,
        embedding_service,
        document_repository,
    ):
        self.storage_service = storage_service
        self.parser_service = parser_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.document_repository = document_repository

    async def process(self, file: UploadFile, user_id: int):

        try:

            # -----------------------------------
            # Save File
            # -----------------------------------

            location = await self.storage_service.save_file(file)

            # -----------------------------------
            # Persist Document Ownership
            # -----------------------------------

            document = Document(
                user_id=user_id,
                filename=file.filename,
                file_path=str(location),
            )

            await self.document_repository.create(document)

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
                f"user_id={user_id}"
            )

            # -----------------------------------
            # Generate Chunks
            # -----------------------------------

            chunks = self.chunking_service.split(
                text=text,
                document_id=database_document_id,
                metadata={
                    "document_id": database_document_id,
                    "user_id": str(user_id),
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

            raise DocumentProcessingException("Unable to process document.") from e
