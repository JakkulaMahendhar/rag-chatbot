from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session

from app.auth.dependencies import get_current_user

from app.services.document_service import DocumentService

from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentResponse])
async def get_documents(
    current_user=Depends(get_current_user), session: AsyncSession = Depends(get_session)
):

    service = DocumentService(session)

    documents = await service.get_user_documents(current_user.id)

    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):

    service = DocumentService(session)

    return await service.get_document(document_id=document_id, user_id=current_user.id)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):

    service = DocumentService(session)

    return await service.delete_document(
        document_id=document_id, user_id=current_user.id
    )
