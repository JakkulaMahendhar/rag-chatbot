from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check"
)
async def health():

    return {

        "status": "healthy",

        "application": "rag-chatbot"

    }   