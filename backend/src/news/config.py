from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

class NewsSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "AI_"
        extra = "ignore"
    Openai_APIKEY:str= Field(default="xxx")

@lru_cache
def get_NewsSettings() -> NewsSettings:
    return NewsSettings()