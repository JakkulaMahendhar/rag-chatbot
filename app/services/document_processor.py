from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import DocumentProcessingException
from app.core.logger import logger

from app.services.embedding import EmbeddingService
from app.services.embedding_storage import EmbeddingStorageService
from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.chunk_storage import ChunkStorageService
from app.services.vector_store import VectorStoreService


class DocumentProcessingService:

    @staticmethod
    async def process(file: UploadFile):

      try:  

        location = await StorageService.save_file(file)

        logger.info("File saved successfully")

        text = ParserService.parse(location)

        logger.info("Document parsed successfully")

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

        logger.info(f"{len(chunks)} chunks generated")

        ChunkStorageService.save(
            document_id=str(document_id),
            chunks=chunks
        )

        embedding_service = EmbeddingService()

        embeddings = embedding_service.generate(chunks)

        logger.info(f"{len(embeddings)} embeddings generated")

        EmbeddingStorageService.save(
            document_id=str(document_id),
            embeddings=embeddings
        )

        VectorStoreService.add(
            chunks=chunks,
            embeddings=embeddings
        )

        logger.info("Embeddings stored in ChromaDB")
        
        return {
            "document_id": str(document_id),
            "filename": location.name,
            "size": location.stat().st_size,
            "extracted_characters": len(text),
            "total_embeddings": len(embeddings),
            "total_chunks": len(chunks)
        }
      except Exception as e:
            logger.exception("Document processing failed")
            raise DocumentProcessingException(
                "Unable to process document."
            ) from e

  