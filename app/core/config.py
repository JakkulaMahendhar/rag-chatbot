from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Application
    project_name: str = "rag-chatbot"


    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"


    # Chunking Configuration
    chunk_size: int = 1000

    chunk_overlap: int = 200


    # Vector Database
    chroma_path: str = "./vector_db"


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()