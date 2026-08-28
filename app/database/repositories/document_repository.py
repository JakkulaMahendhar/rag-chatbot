from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.document import Document
from sqlalchemy import select


class DocumentRepository:
    """
    Repository responsible for all database operations
    related to documents.

    Business logic should not directly interact
    with SQLAlchemy queries.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document):

        self.session.add(document)

        await self.session.commit()

        await self.session.refresh(document)

        return document

    async def get_user_documents(self, user_id: int) -> list[Document]:
        """
        Fetch documents belonging only to
        the authenticated user.

        Example:

        User 1
        -------
        document A
        document B


        User 2
        -------
        document C


        Calling with user_id=1
        returns only A and B.
        """

        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.uploaded_at.desc())
        )

        return result.scalars().all()

    async def get_by_id_and_user(
        self, document_id: int, user_id: int
    ) -> Document | None:
        """
        Fetch document only if it belongs
        to authenticated user.
        """

        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id, Document.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def delete(self, document: Document):
        """
        Delete document database record.
        """

        await self.session.delete(document)

        await self.session.commit()

    async def get_user_document_ids(
        self,
        user_id: int | None = None,
    ) -> list[str]:
        """
        Return all document IDs owned by a user.
        These IDs are later used to restrict
        semantic search to the user's documents.
        """

        result = await self.session.execute(
            select(Document.id).where(Document.user_id == user_id)
        )

        return list(result.scalars().all())

    async def get_pending_documents(self, limit: int = 5) -> list[Document]:
        """
        Fetch documents awaiting processing by the worker,
        oldest first.
        """

        result = await self.session.execute(
            select(Document)
            .where(Document.status == "pending")
            .order_by(Document.uploaded_at.asc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def save(self, document: Document):
        """
        Persist changes to an already-tracked document
        (e.g. status/error_message updates).
        """

        await self.session.commit()

        await self.session.refresh(document)

        return document
