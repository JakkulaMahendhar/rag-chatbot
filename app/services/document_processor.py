from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import DocumentProcessingException
from app.core.logger import logger

from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.chunk_storage import ChunkStorageService
from app.services.embedding import EmbeddingService
from app.services.embedding_storage import EmbeddingStorageService
from app.services.vector_store import VectorStoreService


class DocumentProcessingService:


    @staticmethod
    async def process(file: UploadFile):

        try:

            location = await StorageService.save_file(file)

            text = ParserService.parse(location)


            document_id = uuid4()


            chunker = ChunkingService()


            chunks = chunker.split(
                text=text,
                document_id=document_id,
                metadata={
                    "filename": location.name,
                    "type": location.suffix
                }
            )


            ChunkStorageService.save(
                document_id=str(document_id),
                chunks=chunks
            )


            embedding_service = EmbeddingService()


            embeddings = embedding_service.generate(
                chunks
            )


            EmbeddingStorageService.save(
                document_id=str(document_id),
                embeddings=embeddings
            )


            # Sprint 7.1 change
            vector_store = VectorStoreService()


            vector_store.add_chunks(
                chunks=chunks,
                embeddings=embeddings
            )


            logger.info(
                "Document stored successfully in vector database"
            )


            return {

                "document_id": str(document_id),

                "filename": location.name,

                "size": location.stat().st_size,

                "extracted_characters": len(text),

                "total_chunks": len(chunks),

                "total_embeddings": len(embeddings)

            }


        except Exception as e:

            logger.exception(
                "Document processing failed"
            )

            raise DocumentProcessingException(
                "Unable to process document."
            ) from e