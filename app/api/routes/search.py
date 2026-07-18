from fastapi import APIRouter

from app.schemas.search import (
    SearchRequest
)

from app.models.search import SearchResponse

from app.services.search import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Semantic Search"]
)


@router.post(
    "",
    summary="Semantic Search"
)
def semantic_search(
    request: SearchRequest
):

    service = SearchService()

    results = service.search(
        query=request.query,
        top_k=request.top_k
    )

    return SearchResponse(

        query=request.query,

        results=results

    )