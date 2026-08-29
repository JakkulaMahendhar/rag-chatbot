import asyncio
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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


async def _run_chat(
    request: ChatRequest,
    session: AsyncSession,
    current_user: User,
) -> dict:
    """
    Shared by both POST /chat and POST /chat/stream - runs the full RAG
    pipeline (retrieval, reranking, generation, and the hallucination
    guard's validate-then-maybe-regenerate) to completion and returns the
    final result dict. The pipeline itself never streams and is
    identical either way: /chat/stream only changes how the already-
    decided final answer is delivered to the client afterward.
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

    return await _run_chat(request, session, current_user)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Same RAG pipeline as POST /chat, including the hallucination guard
    running to completion first - this is NOT token-level LLM streaming.
    The full answer is generated and validated (and possibly regenerated)
    before the first chunk is ever sent, so total time-to-final-answer is
    the same as /chat (slightly longer, actually, due to the reveal delay
    below). What changes is that the UI can start rendering text
    immediately as it's revealed, instead of showing a spinner for the
    whole request and then popping the complete answer in at once.

    Any config/auth/quota error (see _run_chat) happens before this
    function starts streaming at all, so those still surface as normal
    HTTP error responses (400/503/500) - only a real answer's reveal
    goes over the event stream below.
    """

    result = await _run_chat(request, session, current_user)

    async def event_stream():

        answer = result["answer"]
        words = answer.split(" ")

        for index, word in enumerate(words):

            chunk = word if index == len(words) - 1 else word + " "

            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            await asyncio.sleep(0.02)

        done_payload = {
            "type": "done",
            "conversation_id": result["conversation_id"],
            "sources": [source.model_dump() for source in result["sources"]],
            "search_evaluation": result["search_evaluation"],
        }

        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            # Some reverse proxies (nginx, and Render's own) buffer
            # responses by default, which would silently defeat
            # streaming entirely - defensive even though it's a no-op
            # against the local dev server.
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )
