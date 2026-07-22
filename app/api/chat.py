from fastapi import APIRouter
from pydantic import BaseModel, Field

# from app.services.chat import ChatService
from app.services.rag_chat import RAGChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

class ChatRequest(BaseModel):

    question: str = Field(
        ...,
        example="Explain RAG"
    ) # type: ignore
    
    conversation_id: str | None = Field(
        default=None,
        example=None
    ) # type: ignore


@router.post("")
def chat(
    request: ChatRequest
):

    service = RAGChatService()


    return service.chat(
        question=request.question,
        conversation_id=request.conversation_id
    )



# @router.post("/")
# def chat(
#     question: str
# ):

#     service = ChatService()


#     answer = service.answer(
#         question,
#         []
#     )


#     return {

#         "question": question,

#         "answer": answer

#     }