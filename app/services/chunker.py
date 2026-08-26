from uuid import UUID

from app.models.chunk import DocumentChunk
from app.core.config import settings


class ChunkingService:

    def __init__(
        self
    ):

        # Deferred import - langchain_text_splitters' own __init__.py pulls
        # in torch/transformers regardless of which splitter class is used
        # (it re-exports token-based splitters too), even though
        # RecursiveCharacterTextSplitter itself needs neither. See
        # app/core/ai_registry.py for the same pattern.
        from langchain_text_splitters import RecursiveCharacterTextSplitter

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