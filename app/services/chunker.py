from uuid import UUID

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.chunk import DocumentChunk
from app.core.config import settings


class ChunkingService:

    def __init__(
        self
    ):

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len
        )


    def split(
        self,
        text: str,
        document_id: UUID,
        metadata: dict
    ) -> list[DocumentChunk]:

        chunks = self.splitter.split_text(text)

        return [
            DocumentChunk(
                chunk_id=index,
                document_id=document_id,
                content=chunk,
                metadata=metadata
            )
            for index, chunk in enumerate(chunks)
        ]