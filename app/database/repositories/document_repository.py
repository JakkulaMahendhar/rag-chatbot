from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.document import Document


class DocumentRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document):

        self.session.add(document)

        await self.session.commit()

        await self.session.refresh(document)

        return document
