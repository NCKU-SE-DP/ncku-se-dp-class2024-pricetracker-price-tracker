class Config:
    class Setting:
        FASTAPI_PREFIX = "/api/v1"
        SENTRY_DSN = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"
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