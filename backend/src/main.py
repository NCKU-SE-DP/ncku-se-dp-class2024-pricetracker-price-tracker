from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import sentry_sdk

from src.models import NewsArticle
from src.auth.database import engine
from .news.utils import get_new
from .auth.database import SessionLocal
from .config import SentryConfig, AppConfig

from .news.router import router as news_router
from .price.router import router as price_router
from .user.router import router as user_router

sentry_sdk.init(
    dsn=SentryConfig.SENTRY_DSN,
    traces_sample_rate=SentryConfig.TRACES_SAMPLE_RATE,
    profiles_sample_rate=SentryConfig.PROFILES_SAMPLE_RATE,
)

app = FastAPI()
bgs = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=AppConfig.CORS_ALLOW_ORIGINS,
    allow_credentials=AppConfig.CORS_ALLOW_CREDENTIALS,
    allow_methods=AppConfig.CORS_ALLOW_METHODS,
    allow_headers=AppConfig.CORS_ALLOW_HEADERS,
)

app.include_router(news_router, prefix="/api/v1", tags=["news"])
app.include_router(price_router, prefix="/api/v1", tags=["prices"])
app.include_router(user_router, prefix="/api/v1", tags=["users"])

@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        get_new()
    db.close()
    bgs.add_job(get_new, "interval", minutes=AppConfig.FETCH_INTERVAL_MINUTES)
    bgs.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    bgs.shutdown()