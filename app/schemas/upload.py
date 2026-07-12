from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    size: int
    extracted_characters: int
    total_chunks: int
    message: str