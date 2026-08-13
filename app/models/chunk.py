from datetime import datetime

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):

    chunk_id: str

    document_id: str

    content: str

    metadata: dict

    created_at: datetime = Field(default_factory=datetime.utcnow)
