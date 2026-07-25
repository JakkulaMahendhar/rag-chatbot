from pydantic import BaseModel


class RAGMetrics(BaseModel):

    conversation_id: str

    question: str

    retrieved_chunks: int

    accepted_chunks: int

    context_length: int

    embedding_time: float

    retrieval_time: float

    llm_time: float

    total_time: float