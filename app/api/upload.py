from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.schemas.upload import UploadResponse
from app.services.document_registration_service import DocumentRegistrationService

from app.auth.dependencies import get_current_user, get_document_registration_service
from app.database.models.user import User
from fastapi import Depends

router = APIRouter()

ALLOWED_TYPES = {".pdf", ".docx", ".txt"}


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Document for Processing",
    description="""
Uploads a document and queues it for background processing.

Pipeline (runs asynchronously in a separate worker):

1. Upload File
2. Store File
3. Parse Text
4. Generate Chunks
5. Generate Embeddings
6. Store Vectors in ChromaDB
7. Index in BM25

Poll GET /documents/{document_id} for status - it moves from
"pending" to "processing", then "completed" or "failed".
""",
    response_model=UploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentRegistrationService = Depends(get_document_registration_service),
):

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    document = await service.register(file=file, user_id=current_user.id)

    return UploadResponse(
        document_id=str(document.id),
        filename=document.filename,
        status=document.status,
        message="Document uploaded and queued for processing.",
    )
