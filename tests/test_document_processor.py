import asyncio

from unittest.mock import AsyncMock, MagicMock

from app.services.document_processor import DocumentProcessingService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.embedding import EmbeddingService
from app.database.models.document import Document


def _build_service(repository):

    return DocumentProcessingService(
        parser_service=ParserService(),
        chunking_service=ChunkingService(),
        embedding_service=EmbeddingService(),
        document_repository=repository,
    )


def test_process_document_success():
    """
    Exercises the real parse -> chunk -> embed -> vector store -> BM25
    pipeline (the worker's job - see app/worker.py) against a document
    row that isn't backed by a real DB session, so this doesn't touch
    the async engine/event loop at all.
    """

    document = Document(
        id=999999,
        user_id=1,
        filename="sample.txt",
        file_path="tests/sample.txt",
        status="pending",
    )

    repository = MagicMock()
    repository.save = AsyncMock(side_effect=lambda doc: doc)

    service = _build_service(repository)

    result = asyncio.run(service.process_document(document))

    assert document.status == "completed"
    assert document.error_message is None
    assert result["total_chunks"] >= 1
    assert result["total_embeddings"] == result["total_chunks"]

    # status transitioned pending -> processing -> completed, each
    # persisted through the repository
    assert repository.save.await_count == 2


def test_process_document_failure_records_error():
    """
    A missing file should fail parsing - process_document should
    catch it, record status="failed" with the error, and re-raise.
    """

    document = Document(
        id=999998,
        user_id=1,
        filename="missing.txt",
        file_path="tests/does_not_exist.txt",
        status="pending",
    )

    repository = MagicMock()
    repository.save = AsyncMock(side_effect=lambda doc: doc)

    service = _build_service(repository)

    try:

        asyncio.run(service.process_document(document))

        assert False, "expected DocumentProcessingException"

    except Exception:

        pass

    assert document.status == "failed"
    assert document.error_message is not None
