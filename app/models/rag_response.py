from pydantic import BaseModel
from typing import List


class HallucinationResult(BaseModel):

    grounded: bool

    confidence: float

    unsupported_claims: List[str]


class RAGResponse(BaseModel):

    answer: str

    sources: list

    hallucination: HallucinationResult
