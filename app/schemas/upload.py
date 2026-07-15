from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    document_id: str
    size: int
    extracted_characters: int
    total_chunks: int
    total_embeddings: int
    message: str