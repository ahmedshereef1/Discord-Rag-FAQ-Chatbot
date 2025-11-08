from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: float
    OPENAI_API_KEY: str | None = None
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE_MB: int
    FILE_DEFAULT_CHUNK_SIZE : int
    MONGO_URL: str
    MONGO_DB_NAME: str
    
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()