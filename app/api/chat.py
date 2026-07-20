from fastapi import APIRouter
from pydantic import BaseModel

# from app.services.chat import ChatService
from app.services.rag_chat import RAGChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

class ChatRequest(BaseModel):

    question: str



@router.post("")
def chat(
    request: ChatRequest
):

    service = RAGChatService()


    return service.chat(
        request.question
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