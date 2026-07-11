from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    size: int
    extracted_characters: int
    message: str