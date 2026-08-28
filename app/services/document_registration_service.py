from fastapi import UploadFile

from app.core.logger import logger
from app.database.models.document import Document


class DocumentRegistrationService:
    """
    Fast phase of document upload: save the file and create a
    pending Document row. Does not parse/chunk/embed - that's
    DocumentProcessingService's job, run by the worker
    (see app/worker.py) so the HTTP request returns immediately
    regardless of document size.
    """

    def __init__(self, storage_service, document_repository):
        self.storage_service = storage_service
        self.document_repository = document_repository

    async def register(self, file: UploadFile, user_id: int) -> Document:

        location = await self.storage_service.save_file(file)

        document = Document(
            user_id=user_id,
            filename=file.filename,
            file_path=str(location),
        )

        await self.document_repository.create(document)

        logger.info(
            f"Document registered for processing | "
            f"document_id={document.id} | user_id={user_id}"
        )

        return document
