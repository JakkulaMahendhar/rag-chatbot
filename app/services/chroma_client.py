import chromadb

from app.core.config import settings


class ChromaClient:


    _client = None


    @classmethod
    def get_client(cls):

        if cls._client is None:

            cls._client = chromadb.PersistentClient(
                path=settings.chroma_path
            )

        return cls._client