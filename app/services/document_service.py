from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.document_repository import DocumentRepository
from fastapi import HTTPException, status

from app.services.bm25_search import BM25SearchService
from app.services.storage import StorageService
from app.services.vector_store import VectorStoreService


class DocumentService:
    """
    Business layer for document operations.

    Router should not directly access repository.
    """

    def __init__(self, session: AsyncSession):

        self.repository = DocumentRepository(session)

    async def get_user_documents(self, user_id: int):
        """
        Return only documents
        belonging to authenticated user.
        """

        return await self.repository.get_user_documents(user_id)

    async def get_document(self, document_id: int, user_id: int):
        """
        Return document only if user owns it.
        """

        document = await self.repository.get_by_id_and_user(document_id, user_id)

        if not document:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document",
            )

        return document

    async def delete_document(self, document_id: int, user_id: int):
        """
        Delete document only if
        authenticated user owns it.
        """

        document = await self.repository.get_by_id_and_user(document_id, user_id)

        if not document:

            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this document",
            )

        # ----------------------------------
        # Delete physical file
        # ----------------------------------

        await StorageService.delete_file(document.file_path)

        # ----------------------------------
        # Delete vector embeddings
        # ----------------------------------

        vector_store = VectorStoreService()

        vector_store.delete_document(str(document.id))

        # ----------------------------------
        # Delete BM25 index
        # ----------------------------------

        bm25_service = BM25SearchService()

        bm25_service.delete_document(str(document.id))

        # ----------------------------------
        # Delete database record
        # ----------------------------------

        await self.repository.delete(document)

        return {"message": "Document deleted successfully"}
