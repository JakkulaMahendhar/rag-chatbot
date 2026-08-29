from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from google.api_core.exceptions import GoogleAPIError
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

    # Optional per-request override of the server's default LLM
    # (settings.llm_provider, "ollama" unless configured otherwise) - lets
    # the frontend's Settings screen switch to Gemini without a restart.
    llm_provider: Literal["ollama", "gemini"] | None = Field(
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

    try:

        service = RAGChatService(
            session=session,
            llm_provider=request.llm_provider,
        )

    except ValueError as error:

        raise HTTPException(status_code=400, detail=str(error))

    try:

        return await service.chat(
            question=request.question,
            conversation_id=request.conversation_id,
            user_id=current_user.id,
        )

    except GoogleAPIError as error:

        # Covers quota/rate-limit errors (e.g. the free tier's 20
        # requests/day cap), auth failures, and other Gemini-side
        # failures - surfaces as a clean, actionable message instead of
        # a bare 500. Deliberately narrow: anything that isn't a Gemini
        # API error (a real bug in our own code, a DB error, ...) is left
        # to raise and surface as a normal 500, unmasked.
        raise HTTPException(
            status_code=503,
            detail=f"Gemini API error: {error.message}",
        )
