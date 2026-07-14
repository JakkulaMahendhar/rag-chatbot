from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class DocumentChunk(BaseModel):

    chunk_id: int

    document_id: UUID

    content: str

    metadata: dict

    created_at: datetime = datetime.utcnow()