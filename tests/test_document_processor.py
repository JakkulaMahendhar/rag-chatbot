import pytest

from unittest.mock import AsyncMock, patch

from fastapi import UploadFile

from app.services.document_processor import DocumentProcessingService


@pytest.mark.asyncio
async def test_document_processing():

    file = UploadFile(
        filename="sample.pdf",
        file=None # pyright: ignore[reportArgumentType]
    )

    with patch(
        "app.services.storage.StorageService.save_file",
        new_callable=AsyncMock
    ):

        pass