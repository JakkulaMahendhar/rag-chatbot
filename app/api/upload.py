from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.upload import UploadResponse
from app.services.document_processor import DocumentProcessingService

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

    try:

        result = await DocumentProcessingService.process(file)

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to process document: {str(e)}"
        )

    return UploadResponse(
        **result,
        message="File uploaded, parsed and chunked successfully"
    )