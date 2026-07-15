from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentEmbedding(BaseModel):

    chunk_id: int

    document_id: UUID

    embedding: list[float]

    metadata: dict

    created_at: datetime = datetime.utcnow()