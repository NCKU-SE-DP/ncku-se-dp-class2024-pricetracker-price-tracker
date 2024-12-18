from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk import init as sentry_init
from apscheduler.schedulers.background import BackgroundScheduler
from .users.router import router as user_router
from .news.router import router as news_router
from .pricing.router import router as pricing_router
from .database import SessionLocal
from .news.service import process_and_store_relevant_news
from .news.models import NewsArticle
from .config import Config
from .exceptions_handler import APIException, InternalServerErrorException
from .logger import logger
sentry_init(
    dsn=Config.Setting.SENTRY_DSN,
    traces_sample_rate=Config.Setting.TRACES_SAMPLE_RATE,
    profiles_sample_rate=Config.Setting.PROFILES_SAMPLE_RATE
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.Setting.CORS_ALLOW_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def initialize_news_scheduler():
    """
    初始化新聞爬取排程
    :param db_session: 用於與新聞資料庫交互的資料庫會話。
    :param background_scheduler: 用於執行定時任務的排程器。
    :return: 無返回值
    """
    
    logger.info("Starting the news fetching job")
    try:
        db_session = SessionLocal()
        if db_session.query(NewsArticle).count() == 0:
            process_and_store_relevant_news()
        db_session.close()
        
        # 設置一個每隔 100 分鐘執行一次的定時任務
        background_scheduler.add_job(process_and_store_relevant_news, "interval", minutes=Config.News.NEWS_FETCH_INTERVAL_TIME)
        background_scheduler.start()
        logger.info("News fetching job started")
    except Exception as e:
        logger.error("Failed to start the news fetching job", exc_info=True)
        raise InternalServerErrorException(e)

@app.on_event("shutdown")
def shutdown_scheduler():
    """
    關閉排程器
    :param background_scheduler: 負責管理定時任務的排程器。
    :return: 無返回值
    """
    logger.info("Shutting down the news fetching job")
    try:
        background_scheduler.shutdown()
        logger.info("News fetching job stopped")
    except Exception as e:
        logger.error("Failed to stop the news fetching job", exc_info=True)
        raise InternalServerErrorException(e)

app.include_router(user_router, prefix=Config.Setting.FASTAPI_PREFIX)
app.include_router(news_router, prefix=Config.Setting.FASTAPI_PREFIX)
app.include_router(pricing_router, prefix=Config.Setting.FASTAPI_PREFIX)

@app.exception_handler(APIException)
async def api_exception_handler(request, exc):
    """
    FastAPI exception handler for APIException.
    :param request: The incoming request.
    :param exc: The raised APIException.
    :return: A JSONResponse containing the exception details.
    """
    exc.handle()
    return exc.to_response()