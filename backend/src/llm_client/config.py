from pydantic_settings import BaseSettings
from functools import lru_cache

from pydantic import Field
class AIConfig(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "AI_"
        extra = "ignore"
    OPENAI_ENABLED : bool = Field(True)
    
    OPEN_AI_KEY: str = Field("")

    OPEN_AI_MODEL: str =Field("gpt-3.5-turbo")
@lru_cache
def get_ai_config() -> AIConfig:
    return AIConfig()