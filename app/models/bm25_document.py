from pydantic import BaseModel


class BM25Document(BaseModel):

    chunk_id: str

    document_id: str

    content: str

    metadata: dict
