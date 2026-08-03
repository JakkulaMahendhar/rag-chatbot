from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.upload import UploadResponse
from app.services.document_processor import DocumentProcessingService

from app.auth.dependencies import get_current_user, get_document_processing_service
from app.database.models.user import User
from fastapi import Depends

router = APIRouter()

ALLOWED_TYPES = {".pdf", ".docx", ".txt"}


@router.post(
    "/upload",
    summary="Upload and Process Document",
    description="""
Uploads a document and executes the complete AI processing pipeline.

Pipeline:

1. Upload File
2. Store File
3. Parse Text
4. Generate Chunks
5. Generate Embeddings
6. Store Vectors in ChromaDB
""",
    response_model=UploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentProcessingService = Depends(get_document_processing_service),
):

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    result = await service.process(file=file, user_id=current_user.id)

    return UploadResponse(
        **result,
        message="Document uploaded, processed, embedded, and indexed successfully."
    )
