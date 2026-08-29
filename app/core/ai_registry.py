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
    _reranker = None


    @classmethod
    def get_embedding_model(cls):

        if cls._embedding_model is None:

            # Deferred import: sentence_transformers pulls in torch, which
            # is expensive to import (not just to load a model with) on a
            # memory/CPU-constrained host. Keeping it out of this module's
            # top-level imports means it isn't paid at process startup at
            # all - only on the first call that actually needs it.
            from sentence_transformers import SentenceTransformer

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


    @classmethod
    def get_reranker(cls):

        if cls._reranker is None:

            # Deferred import: see get_embedding_model() above for why.
            from app.services.reranker import Reranker

            print("Loading cross-encoder reranker: cross-encoder/ms-marco-MiniLM-L-6-v2")

            cls._reranker = Reranker()

        return cls._reranker