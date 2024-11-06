class UserConstants:
    user_max_length = 50
    password_max_length = 200
class SentryConfig:
    SENTRY_DSN = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"
    TRACES_SAMPLE_RATE = 1.0
    PROFILES_SAMPLE_RATE = 1.0
class AppConfig:
    FETCH_INTERVAL_MINUTES = 100
    CORS_ALLOW_ORIGINS = ["http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    INTERVAL_MINUTES = 30