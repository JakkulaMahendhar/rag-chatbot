from pydantic import BaseModel


class SourceReference(BaseModel):

    document_id: str

    chunk_id: str

    filename: str

    content: str

    score: float | None = None