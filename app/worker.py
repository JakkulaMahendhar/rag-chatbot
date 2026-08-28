import asyncio

from app.core.logger import logger
from app.database.session import AsyncSessionLocal
from app.database.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessingService
from app.services.parser import ParserService
from app.services.chunker import ChunkingService
from app.services.embedding import EmbeddingService

POLL_INTERVAL_SECONDS = 5
BATCH_SIZE = 5


async def run():
    """
    Polls for documents awaiting processing and runs the full
    parse/chunk/embed/index pipeline on each one.

    Runs as a separate process from the web app (see
    worker_entrypoint.sh / render.yaml's "worker" service) so that
    /upload can return immediately regardless of document size, and
    so the memory-heavy embedding/chunking dependencies only need to
    fit on this process, not the web-facing one.
    """

    logger.info("Document processing worker started")

    # Constructed once, not per document - each triggers its deferred
    # heavy import the first time it's used, and there's no reason to
    # pay that cost more than once per worker process.
    parser_service = ParserService()
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()

    while True:

        try:

            async with AsyncSessionLocal() as session:

                repository = DocumentRepository(session)

                pending = await repository.get_pending_documents(limit=BATCH_SIZE)

                if pending:

                    processing_service = DocumentProcessingService(
                        parser_service=parser_service,
                        chunking_service=chunking_service,
                        embedding_service=embedding_service,
                        document_repository=repository,
                    )

                    for document in pending:

                        try:

                            await processing_service.process_document(document)

                        except Exception:

                            # process_document already records
                            # status="failed" and logs the exception -
                            # just keep the loop alive for the next
                            # document.
                            logger.exception(
                                f"Worker failed to process document | "
                                f"document_id={document.id}"
                            )

        except Exception:

            # Covers failures before a document is even in hand - e.g.
            # the database isn't reachable yet, or migrations from the
            # web service haven't landed yet. Log and retry next cycle
            # instead of crashing the whole worker process.
            logger.exception("Worker poll cycle failed")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
