from pydantic_settings import BaseSettings
from typing import List , Optional

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: float

    # Backends
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    # API keys + URLs
    OPENAI_API_KEY: str | None = None
    OPENAI_API_URL: str | None = None
    COHERE_API_KEY: str | None = None

    # Model IDs
    GENERATION_MODEL_ID_LITERAL : Optional[List[str]] = None
    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str
    EMBEDDING_MODEL_SIZE: int

    # Defaults / limits
    DEFAULT_INPUT_MAX_CHARACTERS: int
    GENERATION_DEFAULT_MAX_TOKENS: int
    GENERATION_DEFAULT_TEMPERATURE: float

    # Files
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE_MB: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # Mongo
    MONGO_URL: str
    MONGO_DB_NAME: str

    # Vector DB Qdrant 
    VECTOR_DB_BACKEND_LITERAL : Optional[List[str]] = None
    VECTOR_DB_BACKEND: str  
    VECTOR_DB_PATH: str 
    VECTOR_DB_DISTANCE_METHOD: str 
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int

    # Template 
    DEFAULT_LANG : str = "en"
    PRIMARY_LANG : str = "en"

    # Postgress DB
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str 
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
