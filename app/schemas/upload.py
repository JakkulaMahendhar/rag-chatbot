from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    size: int
    message: str