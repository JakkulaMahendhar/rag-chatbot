from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.llm.gemini import GeminiService
from app.services.llm.ollama import OllamaService


class AIServiceRegistry:
    """
    Central registry for AI services.

    Responsible for loading and reusing
    AI models across the application.
    """

    _embedding_model = None
    _llm = None


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



    @classmethod
    def get_llm(cls):

        if cls._llm is None:

            if settings.llm_provider == "gemini":

                cls._llm = GeminiService()


            elif settings.llm_provider == "ollama":

                cls._llm = OllamaService()


            else:

                raise ValueError(
                    f"Unsupported LLM provider: {settings.llm_provider}"
                )


        return cls._llm