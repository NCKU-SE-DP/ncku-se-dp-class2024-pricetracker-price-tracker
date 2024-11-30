import requests
import itertools
from typing import Optional
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Depends, Query
from openai import OpenAI
import json
from ..config import OPENAI_API_KEY, DEFAULT_SCHEDULER_INTERVAL_MINUTES
from ..database import get_db
from ..models import NewsArticle, User
from ..schemas import PromptRequest, NewsSummaryRequestSchema
from sqlalchemy.orm import Session
from ..service import add_news_to_db, get_news_article_upvote_details
from ..dependence import authenticate_user_token
from ..service import toggle_news_article_upvote, fetch_news_info

router = APIRouter()  

@router.post("/api/v1/news/{id}/upvote")
def handle_news_article_upvote(
        id,
        db=Depends(get_db),
        current_user=Depends(authenticate_user_token),
):
    message = toggle_news_article_upvote(id, current_user.id, db)
    return {"message": message}

@router.get("/api/v1/news/user_news")
def get_user_specific_news(
        db=Depends(get_db),
        u=Depends(authenticate_user_token)
):
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_news_article_upvote_details(article.id, u.id, db)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return result

@router.get("/api/v1/news/news")
def get_user_specific_news(
    db: Session = Depends(get_db)
):
    """
    獲取用戶特定的新聞，包括投票狀態
    """
    news_articles = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    user_specific_articles = []
    for article in news_articles:
        upvotes, upvoted = get_news_article_upvote_details(article.id, None, db)
        user_specific_articles.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return user_specific_articles

@router.post("/api/v1/news/news_summary")
async def news_summary(
    payload: NewsSummaryRequestSchema, current_user: User = Depends(authenticate_user_token)
):
    """
    生成新聞摘要
    """
    response = {}
    message_payload = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message_payload,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

_id_counter = itertools.count(start=1000000)

@router.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    """
    提取關鍵字並獲取新聞資料
    """
    prompt = request.prompt
    news_list = []
    keyword_extraction_messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=keyword_extraction_messages,
    )
    extracted_keywords = completion.choices[0].message.content
    # Should change into simple factory pattern
    news_items = fetch_news_info(extracted_keywords, is_initial_fetch=False)
    for news_item in news_items:
        try:
            response = requests.get(news_item["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # Title
            article_title = soup.find("h1", class_="article-content__title").text
            article_time = soup.find("time", class_="article-content__time").text
            # Locate the <section> containing article content
            content_section = soup.find("section", class_="article-content__editor")

            article_paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            article_details = {
                "url": news_item["titleLink"],
                "title": article_title,
                "time": article_time,
                "content": article_paragraphs,
            }
            article_details["content"] = " ".join(article_details["content"])
            article_details["id"] = next(_id_counter)
            news_list.append(article_details)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)