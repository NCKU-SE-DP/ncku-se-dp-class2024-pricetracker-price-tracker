import os
# 資料庫連接 URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///news_database.db")

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "1892dhianiandowqd0n")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DEFAULT_TOKEN_EXPIRE_MINUTES = int(os.getenv("DEFAULT_TOKEN_EXPIRE_MINUTES", 15))

# Sentry 配置
SENTRY_DSN = os.getenv("SENTRY_DSN", "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", 1.0))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", 1.0))

# OpenAI API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")  # 確保替換為您的 OpenAI API 金鑰

# 背景任務排程間隔
DEFAULT_SCHEDULER_INTERVAL_MINUTES = int(os.getenv("DEFAULT_SCHEDULER_INTERVAL_MINUTES", 100))

# CORS 配置
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8080").split(",")
INITIAL_FETCH_PAGE_RANGE = range(1, 10)
