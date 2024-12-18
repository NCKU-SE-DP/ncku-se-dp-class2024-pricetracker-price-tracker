class Config:
    class Setting:
        FASTAPI_PREFIX = "/api/v1"
        SENTRY_DSN = "https://06831ece27fa09a5a4f2a3e3de21518f@o4508489109209088.ingest.us.sentry.io/4508489123627008"
        TRACES_SAMPLE_RATE = 1.0
        PROFILES_SAMPLE_RATE = 1.0
        CORS_ALLOW_ORIGINS = "http://localhost:8080"
    class Auth:
        MAX_USERNAME_SIZE = 50
        MAX_PASSWORD_SIZE = 200
        TOKEN_URL = "/api/v1/users/login"
        SECRET_KEY = "1892dhianiandowqd0n"
        HASHED_METHOD = "HS256"
        TOKEN_EXPIRE_TIME = 30
    class News:
        NEWS_FETCH_INTERVAL_TIME = 100
    class OpenAI:
        OPENAI_TOKEN = ""