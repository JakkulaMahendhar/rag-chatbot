from uuid import UUID

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.chunk import DocumentChunk


class ChunkingService:

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
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