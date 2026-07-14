from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.chunk_storage import ChunkStorageService


class DocumentProcessingService:

    @staticmethod
    async def process(file: UploadFile):

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

        return {
            "document_id": str(document_id),
            "filename": location.name,
            "size": location.stat().st_size,
            "extracted_characters": len(text),
            "total_chunks": len(chunks)
        }