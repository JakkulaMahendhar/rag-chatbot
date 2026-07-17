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

    collection = VectorStoreService.get_collection()

    return {

        "collection": collection.name,

        "vectors": collection.count()

    }