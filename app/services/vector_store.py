from app.models.chunk import DocumentChunk
from app.models.embedding import DocumentEmbedding
from app.services.chroma_client import ChromaClient


class VectorStoreService:

    COLLECTION_NAME = "documents"

    @classmethod
    def get_collection(cls):

        client = ChromaClient.get_client()

        return client.get_or_create_collection(
            name=cls.COLLECTION_NAME
        )

    @classmethod
    def add(
        cls,
        chunks: list[DocumentChunk],
        embeddings: list[DocumentEmbedding]
    ):

        collection = cls.get_collection()

        collection.add(
    ids=[
        str(chunk.chunk_id)
        for chunk in chunks
    ],
    documents=[
        chunk.content
        for chunk in chunks
    ],
    embeddings=[
        embedding.embedding
        for embedding in embeddings
    ],
    metadatas=[
        {
            key: str(value) if value is not None else ""
            for key, value in chunk.metadata.items()
        }
        for chunk in chunks
    ]
)