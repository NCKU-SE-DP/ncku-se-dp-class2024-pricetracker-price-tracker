import json
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, insert
from .config import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, INITIAL_FETCH_PAGE_RANGE, DEFAULT_TOKEN_EXPIRE_MINUTES
from .models import User, NewsArticle, user_news_association_table
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from urllib.parse import quote
from fastapi import Depends
from .database import get_db

# 設定密碼加密上下文
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證用戶輸入的密碼是否與儲存的加密密碼匹配
    """
    return password_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """
    將用戶密碼加密以進行安全存儲
    """
    return password_context.hash(password)

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


def add_news_to_db(news_data: dict, db: Session):
    """
    將新聞資料添加到資料庫中
    """
    news_article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),
        summary=news_data["summary"],
        reason=news_data["reason"],
    )
    db.add(news_article)
    db.commit()

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
def get_all_news_articles(db=Depends(get_db)):
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
def news_exists(id2, db: Session):
    return db.query(NewsArticle).filter_by(id=id2).first() is not None

