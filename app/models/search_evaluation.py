from pydantic import BaseModel


class SearchEvaluation(BaseModel):

    question: str

    vector_results: int

    bm25_results: int

    hybrid_results: int

    best_score: float

    average_score: float

    quality: str