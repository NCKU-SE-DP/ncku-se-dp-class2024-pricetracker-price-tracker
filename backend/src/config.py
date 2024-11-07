from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

class MainSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "MAIN_"
        extra = "ignore"
    FASTAPI_PRIFIX: str = Field(default='/api/v1')

@lru_cache
def get_main_settings() -> MainSettings:
    return MainSettings()