from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    project_name: str = "rag-chatbot"

    # ------------------------------------------------------------------
    # Embedding Configuration
    # ------------------------------------------------------------------
    embedding_model: str = "all-MiniLM-L6-v2"

    # ------------------------------------------------------------------
    # Chunking Configuration
    # ------------------------------------------------------------------
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # ------------------------------------------------------------------
    # Vector Database
    # ------------------------------------------------------------------
    chroma_path: str = "./vector_db"

    # ------------------------------------------------------------------
    # LLM Configuration
    # ------------------------------------------------------------------
    # LLM Configuration

    llm_provider: str = "ollama"

    # llm_provider: str = "gemini"

    gemini_api_key: str | None = None

    gemini_model: str = "gemini-2.5-flash"

    # Ollama

    ollama_model: str = "llama3.1"

    retrieval_top_k: int = 3

    distance_threshold: float = 1.0

    similarity_threshold: float = 0.75

    hybrid_similarity_threshold: float = 0.25

    bm25_path: str = "./storage/bm25"

    vector_weight: float = 0.6

    bm25_weight: float = 0.4

    # Vector Retrieval
    top_k_vector: int = 10

    # BM25 Retrieval
    top_k_BM25: int = 10

    # Hybrid Search
    hybrid_top_k: int = 10

    # Reranking
    rerank_top_k: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

print(settings.gemini_api_key)
print(settings.gemini_model)
print(settings.llm_provider)
