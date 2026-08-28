from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: int

    filename: str

    file_path: str

    uploaded_at: datetime

    status: str

    error_message: str | None = None

    class Config:
        from_attributes = True
