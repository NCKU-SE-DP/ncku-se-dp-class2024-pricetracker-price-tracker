from pydantic_settings import BaseSettings
import os 
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".env"))

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///news_database.db"
    SECRET_KEY: str = "1892dhianiandowqd0n"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = f"{os.getenv('OPENAI_API_KEY')}"
    CLAUDE_API_KEY: str = f"{os.getenv('CLAUDE_API_KEY')}"
    SENTRY_DSN: str = f"{os.getenv('SENTRY_DSN')}"
    CORS_ORIGINS: list = ["http://localhost:8080"]

settings = Settings() 