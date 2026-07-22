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

        document_chunks = []

        for index, chunk in enumerate(chunks):

            chunk_id = f"{document_id}-{index}"

            document_chunks.append(

                DocumentChunk(

                    chunk_id=chunk_id,

                    document_id=document_id,

                    content=chunk,

                    metadata={
                        **metadata,
                        "chunk_id": chunk_id
                    }

                )

            )

        return document_chunks