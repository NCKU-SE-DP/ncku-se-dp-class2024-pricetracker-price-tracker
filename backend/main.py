import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()
# Constants
DEFAULT_SCHEDULER_INTERVAL_MINUTES = 100  # Scheduler interval in minutes for fetching news
INITIAL_FETCH_PAGE_RANGE = range(1, 10)  # Default page range for initial fetch
JWT_SECRET_KEY = '1892dhianiandowqd0n'  # Secret key for JWT encoding and decoding
ID_COUNTER_START = 1000000  # Starting value for custom ID counter

# Load configurations from environment variables or set default values
SENTRY_DSN = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"
SENTRY_TRACES_SAMPLE_RATE = 1.0
SENTRY_PROFILES_SAMPLE_RATE = 1.0
DATABASE_URL = "sqlite:///news_database.db"

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

# from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )


engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
)

app = FastAPI()
bgs = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from openai import OpenAI


# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def add_news_to_db(news_data):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()

#p2 ➔ query_params
#p ➔ page_number
#l ➔ page
def fetch_news_info(search_term, is_initial_fetch=False):
    """
    get new

    :param search_term:
    :param is_initial_fetch:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial_fetch:
        page_results = []
        for page_number in INITIAL_FETCH_PAGE_RANGE:
            query_params = {
                "page": page_number,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=query_params)
            page_results.append(response.json()["lists"])

        for page in page_results:
            all_news_data.append(page)
    else:
        query_params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=query_params)

        all_news_data = response.json()["lists"]
    return all_news_data

#p ➔ paragraph
#m ➔ message_payload
#result ➔ summary_result
#soup ➔ parsed_html_content
#title ➔ article_title
def fetch_and_store_news(is_initial_fetch=False):
    """
    get new info

    :param is_initial_fetch:
    :return:
    """
    news_data = fetch_news_info("價格", is_initial_fetch=is_initial_fetch)
    for news in news_data:
        title = news["title"]
        message_payload = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{title}"},
        ]
        ai = OpenAI(api_key="xxx").chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message_payload,
        )
        relevance_score = ai.choices[0].message.content
        if relevance_score == "high":
            response = requests.get(news["titleLink"])
            parsed_html_content = BeautifulSoup(response.text, "html.parser")
            # 標題
            article_title = parsed_html_content.find("h1", class_="article-content__title").text
            time = parsed_html_content.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = parsed_html_content.find("section", class_="article-content__editor")

            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news = {
                "url": news["titleLink"],
                "title": article_title,
                "time": time,
                "content": paragraphs,
            }
            message_payload = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(detailed_news["content"])},
            ]

            completion = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message_payload,
            )
            summary_result = completion.choices[0].message.content
            summary_result = json.loads(summary_result)
            detailed_news["summary"] = summary_result["影響"]
            detailed_news["reason"] = summary_result["原因"]
            add_news_to_db(detailed_news)



@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        fetch_and_store_news()
    db.close()
    bgs.add_job(fetch_and_store_news, "interval", minutes=DEFAULT_SCHEDULER_INTERVAL_MINUTES)
    bgs.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    bgs.shutdown()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


#p1 ➔ plain_password
#p2 ➔ hashed_password
def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)

#n ➔ username
#password ➔ input_password
def is_user_password_correct(db, username, input_password):
    user = db.query(User).filter(User.username == username).first()
    if not verify_password(input_password, user.hashed_password):
        return False
    return user


def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(session_opener)
):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return db.query(User).filter(User.username == payload.get("sub")).first()

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Access token expiration time in minutes
DEFAULT_TOKEN_EXPIRE_MINUTES = 15  # Default token expiration time in minutes
def create_access_token(data, expires_delta=None):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """login"""
    user = is_user_password_correct(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str
@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """create user"""
    hashed_password = password_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/v1/users/me")
def get_logged_in_user(user=Depends(authenticate_user_token)):
    return {"username": user.username}


_id_counter = itertools.count(start=ID_COUNTER_START)


def get_news_article_upvote_details(article_id, uid, db):
    cnt = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    voted = False
    if uid:
        voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=uid)
                .first()
                is not None
        )
    return cnt, voted

#n ➔ article
#result ➔ formatted_articles
#news ➔ news_articles
@app.get("/api/v1/news/news")
def get_all_news_articles(db=Depends(session_opener)):
    """
    read new

    :param db:
    :return:
    """
    news_articles = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    formatted_articles = []
    for article in news_articles:
        upvotes, upvoted = get_news_article_upvote_details(article.id, None, db)
        formatted_articles.append(
            {**article.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
        )
    return formatted_articles


@app.get(
    "/api/v1/news/user_news"
)
#u ➔ current_user
#result ➔ user_specific_articles
def get_user_specific_news(
        db=Depends(session_opener),
        current_user=Depends(authenticate_user_token)
):
    """
    read user new

    :param db:
    :param u:
    :return:
    """
    news_articles = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    user_specific_articles = []
    for article in news_articles:
        upvotes, upvoted = get_news_article_upvote_details(article.id, current_user.id, db)
        user_specific_articles.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return user_specific_articles

class PromptRequest(BaseModel):
    prompt: str

OPENAI_API_KEY = "xxx"
#m ➔ message_payload
#soup ➔ parsed_article_content
#title ➔ article_title
#time ➔ article_time
#p ➔ paragraph
@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    prompt = request.prompt
    news_list = []
    message_payload = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message_payload,
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_items = fetch_news_info(keywords, is_initial_fetch=False)
    for news in news_items:
        try:
            response = requests.get(news["titleLink"])
            parsed_article_content = BeautifulSoup(response.text, "html.parser")
            # 標題
            article_title = parsed_article_content.find("h1", class_="article-content__title").text
            article_time = parsed_article_content.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = parsed_article_content.find("section", class_="article-content__editor")

            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news = {
                "url": news["titleLink"],
                "title": article_title,
                "time": article_time,
                "content": paragraphs,
            }
            detailed_news["content"] = " ".join(detailed_news["content"])
            detailed_news["id"] = next(_id_counter)
            news_list.append(detailed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSumaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, u=Depends(authenticate_user_token)
):
    response = {}
    m = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=m,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

#u ➔ current_user
@app.post("/api/v1/news/{id}/upvote")
def handle_news_article_upvote(
        id,
        db=Depends(session_opener),
        current_user=Depends(authenticate_user_token),
):
    message = toggle_news_article_upvote(id, current_user.id, db)
    return {"message": message}


def toggle_news_article_upvote(username_id, u_id, db):
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == username_id,
            user_news_association_table.c.user_id == u_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == username_id,
            user_news_association_table.c.user_id == u_id,
        )
        db.execute(delete_stmt)
        db.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=username_id, user_id=u_id
        )
        db.execute(insert_stmt)
        db.commit()
        return "Article upvoted"


def news_exists(id2, db: Session):
    return db.query(NewsArticle).filter_by(id=id2).first() is not None


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()