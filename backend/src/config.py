from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///news_database.db"
    SECRET_KEY: str = "1892dhianiandowqd0n"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = "xxx"
    SENTRY_DSN: str = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"
    CORS_ORIGINS: list = ["http://localhost:8080"]

settings = Settings() 