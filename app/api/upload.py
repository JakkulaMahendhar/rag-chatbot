from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from app.services.parser import ParserService
from app.services.storage import StorageService
from app.schemas.upload import UploadResponse

router = APIRouter()

ALLOWED_TYPES = {
    ".pdf",
    ".docx",
    ".txt"
}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing"
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    location = await StorageService.save_file(file)

# try:
    text = ParserService.parse(location)

# except Exception:
#     raise HTTPException(
#         status_code=400,
#         detail="Unable to parse document"
#     )

    return UploadResponse(
        filename=location.name,
        size=location.stat().st_size,
        extracted_characters=len(text),
        message="File uploaded successfully"
    )