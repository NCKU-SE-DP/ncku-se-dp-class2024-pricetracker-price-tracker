from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "AUTH_"
        extra = "ignore"
    ACCESS_TOKEN_SECRET_KEY: str = Field(default='1892dhianiandowqd0n')
    ACCESS_TOKEN_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)

@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()