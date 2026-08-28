import chromadb

from app.core.config import settings


class ChromaClient:
    """
    Single shared client per process, connecting to the Chroma server
    (docker-compose's "chroma" service) over HTTP rather than opening
    an embedded PersistentClient - see app/core/config.py for why.
    """

    _client = None

    @classmethod
    def get_client(cls):

        if cls._client is None:

            cls._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )

        return cls._client