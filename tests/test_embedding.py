from uuid import uuid4

from app.models.chunk import DocumentChunk
from app.services.embedding import EmbeddingService


def test_embedding_generation():

    chunk = DocumentChunk(
        chunk_id=1,
        document_id=uuid4(),
        content="Artificial Intelligence",
        metadata={}
    )

    service = EmbeddingService()

    embeddings = service.generate([chunk])

    assert len(embeddings) == 1
    assert len(embeddings[0].embedding) == 384