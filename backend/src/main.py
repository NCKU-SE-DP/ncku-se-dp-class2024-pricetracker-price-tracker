from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from config import settings
from database import engine, Base, SessionLocal
from models import NewsArticle
from auth.auth import router as auth_router
from news.news import router as news_router
from prices.prices import router as prices_router
from news import news

# Initialize database
Base.metadata.create_all(bind=engine)

# Initialize Sentry
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
scheduler = BackgroundScheduler()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(prices_router)

async def scheduled_news_update():
    db = SessionLocal()
    try:
        await news.get_new(db)
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Initialize news database if empty
    db = SessionLocal()
    try:
        if db.query(NewsArticle).count() == 0:
            await news.get_new(db, is_initial=True)
    finally:
        db.close()
    
    # Start scheduler
    scheduler.add_job(scheduled_news_update, "interval", minutes=100)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown() 