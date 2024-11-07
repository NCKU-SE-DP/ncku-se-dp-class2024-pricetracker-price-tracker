
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from .news.router import router as news_router
from .users.router import router as users_router
from .prices.router import router as prices_router
from .database import SessionLocal
from .news.service import (get_new_info)
from .news.models import NewsArticle
from .config import get_main_settings
main_settings=get_main_settings()
sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
Scheduler = BackgroundScheduler()


app.include_router(news_router, prefix=main_settings.FASTAPI_PRIFIX)
app.include_router(users_router, prefix=main_settings.FASTAPI_PRIFIX)
app.include_router(prices_router, prefix=main_settings.FASTAPI_PRIFIX)


app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def start_scheduler():
    database = SessionLocal()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        get_new_info()
    database.close()
    Scheduler.add_job(get_new_info, "interval", minutes=100)
    Scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    Scheduler.shutdown()

