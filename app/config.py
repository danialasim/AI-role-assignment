from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    anthropic_api_key: str
    serpapi_key: str = ""
    database_url: str = "sqlite:///./seo_content.db"
    environment: str = "development"
    mock_llm: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()