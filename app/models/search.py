from pydantic import BaseModel


class SearchResult(BaseModel):

    chunk_id: str

    document: str

    metadata: dict

    score: float


class SearchResponse(BaseModel):

    query: str

    results: list[SearchResult]