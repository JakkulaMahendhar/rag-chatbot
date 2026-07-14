from uuid import uuid4

from app.services.chunker import ChunkingService


def test_chunking():

    text = "Artificial Intelligence " * 500

    service = ChunkingService()

    chunks = service.split(
        text=text,
        document_id=uuid4(),
        metadata={
            "filename": "test.pdf",
            "type": ".pdf"
        }
    )

    assert len(chunks) > 1


def test_chunk_metadata():

    service = ChunkingService()

    chunks = service.split(
        text="Artificial Intelligence " * 500,
        document_id=uuid4(),
        metadata={
            "filename": "test.pdf",
            "type": ".pdf"
        }
    )

    assert chunks[0].metadata["filename"] == "test.pdf"
    assert chunks[0].metadata["type"] == ".pdf"