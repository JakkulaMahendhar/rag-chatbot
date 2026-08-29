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
    _llms: dict = {}
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
    def get_llm(cls, provider: str | None = None):

        # `provider` lets a caller (e.g. a per-request "use Gemini instead
        # of Ollama" toggle from the frontend) override the server's
        # configured default without changing global settings. Falls back
        # to settings.llm_provider when not given, same as before.
        provider = provider or settings.llm_provider

        if provider not in cls._llms:

            if provider == "gemini":

                if not settings.gemini_api_key:

                    raise ValueError(
                        "Gemini is not configured on this server "
                        "(GEMINI_API_KEY is not set)."
                    )

                cls._llms[provider] = GeminiService()


            elif provider == "ollama":

                cls._llms[provider] = OllamaService()


            else:

                raise ValueError(
                    f"Unsupported LLM provider: {provider}"
                )


        return cls._llms[provider]


    @classmethod
    def get_reranker(cls):

        if cls._reranker is None:

            # Deferred import: see get_embedding_model() above for why.
            from app.services.reranker import Reranker

            print("Loading cross-encoder reranker: cross-encoder/ms-marco-MiniLM-L-6-v2")

            cls._reranker = Reranker()

        return cls._reranker