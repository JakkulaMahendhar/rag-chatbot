from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository
from app.auth.security import hash_password
from app.auth.security import verify_password
from app.auth.jwt import create_access_token


class AuthService:

    def __init__(self, session: AsyncSession):

        self.repository = UserRepository(session)

    async def register(self, email: str, password: str):

        existing_user = await self.repository.get_by_email(email)

        if existing_user:
            raise ValueError("Email already registered")

        self.validate_password(password)

        user = User(email=email, hashed_password=hash_password(password))

        return await self.repository.create(user)

    async def login(self, email: str, password: str):

        user = await self.repository.get_by_email(email)

        if not user:

            raise ValueError("Invalid email or password")

        if not verify_password(password, user.hashed_password):

            raise ValueError("Invalid email or password")

        token = create_access_token({"sub": str(user.id), "email": user.email})

        return token

    @staticmethod
    def validate_password(password: str):

        password_bytes = len(password.encode("utf-8"))

        if password_bytes < 8:
            raise ValueError("Password must contain at least 8 characters")

        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes")
