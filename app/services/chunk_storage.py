import json
from pathlib import Path

from app.models.chunk import DocumentChunk


class ChunkStorageService:


    STORAGE_PATH = Path("chunks")


    @classmethod
    def save(
        cls,
        document_id: str,
        chunks: list[DocumentChunk]
    ):

        cls.STORAGE_PATH.mkdir(
            exist_ok=True
        )


        file = (
            cls.STORAGE_PATH /
            f"{document_id}.json"
        )


        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                [
                    chunk.model_dump()
                    for chunk in chunks
                ],
                f,
                indent=4,
                default=str
            )