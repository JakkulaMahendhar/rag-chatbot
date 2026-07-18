from pydantic import BaseModel, Field


class SearchRequest(BaseModel):

    query: str = Field(
        min_length=3,
        description="User search query"
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of relevant chunks to retrieve"
    )