from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.core.rate_limiter import InMemoryRateLimiter, rate_limit_dependency

from app.database.models.user import User
from app.database.session import get_session

from app.auth.schemas import RegisterRequest, UserResponse

from app.auth.service import AuthService

from app.auth.schemas import LoginRequest, TokenResponse

from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

_auth_rate_limiter = InMemoryRateLimiter(
    max_attempts=settings.auth_rate_limit_attempts,
    window_seconds=settings.auth_rate_limit_window_seconds,
)

_rate_limited = Depends(rate_limit_dependency(_auth_rate_limiter))


@router.post(
    "/register", response_model=UserResponse, dependencies=[_rate_limited]
)
async def register(
    request: RegisterRequest, session: AsyncSession = Depends(get_session)
):

    service = AuthService(session)

    try:

        user = await service.register(request.email, request.password)

        return user

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/login", response_model=TokenResponse, dependencies=[_rate_limited]
)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)):

    service = AuthService(session)

    try:

        token = await service.login(request.email, request.password)

        return {"access_token": token, "token_type": "bearer"}

    except ValueError as e:

        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):

    return {"id": current_user.id, "email": current_user.email}
