from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # =====================================================
    # Application
    # =====================================================

    project_name: str = "rag-chatbot"

    # Database
    DATABASE_URL: str

    # Sync database URL for Alembic
    DATABASE_URL_SYNC: str

    # JWT Configuration

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    jwt_expiration_minutes: int = 30

    # =====================================================
    # Embeddings
    # =====================================================

    embedding_model: str = "all-MiniLM-L6-v2"

    # =====================================================
    # Chunking
    # =====================================================

    chunk_size: int = 1000
    chunk_overlap: int = 200

    # =====================================================
    # Vector Database
    #
    # Chroma runs as its own server (docker-compose's "chroma" service),
    # not as an embedded PersistentClient - the app and worker are
    # separate processes, and Chroma's embedded storage isn't designed
    # for concurrent access from more than one process at a time (this
    # was the root cause of intermittent "Error finding id" failures).
    # =====================================================

    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # =====================================================
    # LLM
    # =====================================================

    llm_provider: str = "ollama"

    ollama_model: str = "llama3.1"

    gemini_api_key: str | None = None

    gemini_model: str = "gemini-3.6-flash"

    # =====================================================
    # Retrieval Configuration
    # =====================================================

    # Final number of documents returned to pipeline

    retrieval_top_k: int = 5

    # -----------------------------
    # Vector Search
    # -----------------------------

    top_k_vector: int = 10

    # Chroma distance cutoff
    #
    # Smaller = better similarity
    #
    # cosine distance:
    # 0 = identical
    # 1 = unrelated

    vector_distance_threshold: float = 0.75

    # Convert distance to similarity score

    vector_similarity_threshold: float = 0.25

    # -----------------------------
    # BM25
    # -----------------------------

    top_k_bm25: int = 10

    # -----------------------------
    # Hybrid Search
    # -----------------------------

    vector_weight: float = 0.6

    bm25_weight: float = 0.4

    hybrid_top_k: int = 10

    # Final acceptance threshold

    hybrid_score_threshold: float = 0.30

    # -----------------------------
    # Reranking
    # -----------------------------

    rerank_top_k: int = 3

    reranker_score_threshold: float = 0.20

    # =====================================================
    # BM25 Storage
    # =====================================================

    bm25_path: str = "./storage/bm25"

    # Hallucination Guard

    enable_hallucination_guard: bool = True

    hallucination_threshold: float = 0.75

    # =====================================================
    # CORS
    # =====================================================

    # Comma-separated list of allowed origins, or "*" for all
    allowed_origins: str = "*"

    # =====================================================
    # Auth Rate Limiting
    # =====================================================

    auth_rate_limit_attempts: int = 5

    auth_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
