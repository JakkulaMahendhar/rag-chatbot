from sqlalchemy import select

from app.database.models.user import User


class UserRepository:

    def __init__(self, session):

        self.session = session

    async def get_by_email(self, email: str):

        result = await self.session.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def create(self, user: User):

        self.session.add(user)

        await self.session.commit()

        await self.session.refresh(user)

        return user

    async def get_by_id(self, user_id: int):

        result = await self.session.execute(select(User).where(User.id == user_id))

        return result.scalar_one_or_none()
