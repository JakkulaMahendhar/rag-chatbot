from fastapi import APIRouter

from app.services.chat import ChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)



@router.post("/")
def chat(
    question: str
):

    service = ChatService()


    answer = service.answer(
        question,
        []
    )


    return {

        "question": question,

        "answer": answer

    }