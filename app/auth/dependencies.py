from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_session
from app.database.models.user import User
from app.database.repositories.user_repository import UserRepository

from app.services.document_registration_service import DocumentRegistrationService
from app.services.storage import StorageService

from app.database.repositories.document_repository import DocumentRepository
from app.database.session import get_session

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:

        raise HTTPException(status_code=401, detail="Invalid token")

    repository = UserRepository(session)

    user = await repository.get_by_id(int(user_id))

    if not user:

        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_document_registration_service(session=Depends(get_session)):

    return DocumentRegistrationService(
        storage_service=StorageService(),
        document_repository=DocumentRepository(session),
    )
