from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):

    chunk_id: str

    document_id: UUID

    content: str

    metadata: dict

    created_at: datetime = Field(default_factory=datetime.utcnow)