import json
from pathlib import Path

from app.models.embedding import DocumentEmbedding


class EmbeddingStorageService:

    STORAGE_PATH = Path("embeddings")

    @classmethod
    def save(
        cls,
        document_id: str,
        embeddings: list[DocumentEmbedding]
    ):

        cls.STORAGE_PATH.mkdir(exist_ok=True)

        file = cls.STORAGE_PATH / f"{document_id}.json"

        with open(file, "w", encoding="utf-8") as f:

            json.dump(
                [
                    embedding.model_dump()
                    for embedding in embeddings
                ],
                f,
                indent=4,
                default=str
            )