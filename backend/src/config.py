class UserConstants:
    user_max_length = 50
    password_max_length = 200
class SentryConfig:
    SENTRY_DSN = "https://c6c709168e44059051c29975c9fd0c66@o4508454866780160.ingest.us.sentry.io/4508454877921280"
    TRACES_SAMPLE_RATE = 1.0
    PROFILES_SAMPLE_RATE = 1.0
class AppConfig:
    FETCH_INTERVAL_MINUTES = 100
    CORS_ALLOW_ORIGINS = ["http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    INTERVAL_MINUTES = 30
class OpenAIConfig:
    MODEL_NAME = "gpt-3.5-turbo"