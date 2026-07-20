from fastapi import APIRouter

from app.services.vector_store import VectorStoreService

router = APIRouter(
    prefix="/vectors",
    tags=["Vectors"]
)


@router.get(
    "/stats",
    summary="Vector Database Statistics"
)
def stats():

    vector_store = VectorStoreService()

    return vector_store.stats()