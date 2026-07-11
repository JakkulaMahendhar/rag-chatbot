from pathlib import Path
from fastapi import UploadFile
from uuid import uuid4
import shutil

UPLOAD_DIR = Path("uploads")


class StorageService:

    @staticmethod
    async def save_file(file: UploadFile):

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not file.filename:
            raise ValueError("Filename missing")

        extension = Path(file.filename).suffix
        filename = f"{uuid4()}{extension}"

        destination = UPLOAD_DIR / filename

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return destination