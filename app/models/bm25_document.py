from pydantic import BaseModel
from uuid import UUID


class BM25Document(BaseModel):

    chunk_id: str

    document_id: UUID

    content: str

    metadata: dict