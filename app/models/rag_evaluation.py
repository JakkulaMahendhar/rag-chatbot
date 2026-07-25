from pydantic import BaseModel


class RAGEvaluation(BaseModel):

    question: str

    retrieved_chunks: int

    average_score: float

    best_score: float

    worst_score: float

    quality: str