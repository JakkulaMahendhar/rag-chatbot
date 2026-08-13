from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.database.models.user import User
from app.services.rag_chat import RAGChatService
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):

    question: str = Field(
        ...,
        example="Explain RAG",
    )

    conversation_id: str | None = Field(
        default=None,
        example=None,
    )


@router.post("")
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Execute RAG chat for the authenticated user.

    The authenticated user's ID is passed to the RAG
    pipeline so retrieval is restricted to documents
    owned by that user.
    """

    service = RAGChatService(
        session=session,
    )

    return await service.chat(
        question=request.question,
        conversation_id=request.conversation_id,
        user_id=current_user.id,
    )
