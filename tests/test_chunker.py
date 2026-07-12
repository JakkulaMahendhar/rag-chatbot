from app.services.chunker import ChunkingService


def test_chunking():

    text = "Artificial Intelligence " * 500

    service = ChunkingService()

    chunks = service.split(text)

    assert len(chunks) > 1