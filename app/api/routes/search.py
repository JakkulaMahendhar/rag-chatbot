from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.database.models.user import User
from app.auth.dependencies import get_current_user
from app.models.search import SearchResponse
from app.schemas.search import SearchRequest
from app.services.search import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Semantic Search"],
)


@router.post(
    "",
    response_model=SearchResponse,
    summary="Semantic Search",
)
async def semantic_search(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = SearchService(
        session=session,
    )

    results = await service.search(
        query=request.query,
        top_k=request.top_k,
        user_id=current_user.id,
    )

    return SearchResponse(
        query=request.query,
        results=results,
    )
