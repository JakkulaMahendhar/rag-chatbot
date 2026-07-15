from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    embedding_model: str = "all-MiniLM-L6-v2"

    chunk_size: int = 1000

    chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()