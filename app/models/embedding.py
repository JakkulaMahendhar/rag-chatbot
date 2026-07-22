from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentEmbedding(BaseModel):

    chunk_id: str

    document_id: UUID

    embedding: list[float]

    metadata: dict

    created_at: datetime = Field(default_factory=datetime.utcnow)