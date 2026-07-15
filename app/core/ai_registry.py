from sentence_transformers import SentenceTransformer

from app.core.config import settings


class AIServiceRegistry:
    """
    Central registry for AI services.

    Responsible for loading and reusing
    AI models across the application.
    """

    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):

        if cls._embedding_model is None:

            print(
                f"Loading embedding model: {settings.embedding_model}"
            )

            cls._embedding_model = SentenceTransformer(
                settings.embedding_model
            )

        return cls._embedding_model