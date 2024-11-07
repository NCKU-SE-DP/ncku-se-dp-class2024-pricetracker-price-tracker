import requests
from typing import Optional
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Depends, Query
from openai import OpenAI
from ..config import OPENAI_API_KEY, DEFAULT_SCHEDULER_INTERVAL_MINUTES
from ..database import get_db
from ..models import NewsArticle, User
from ..schemas import PromptRequest, NewsSummaryRequestSchema
from sqlalchemy.orm import Session
from ..service import add_news_to_db, get_news_article_upvote_details
from ..dependence import authenticate_user_token

router = APIRouter(
    prefix="/api/v1/news"
)  

@router.get("/news")
def get_user_specific_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticate_user_token)
):
    """
    獲取用戶特定的新聞，包括投票狀態
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

@router.post("/news_summary")
async def news_summary(
    payload: NewsSummaryRequestSchema, current_user: User = Depends(authenticate_user_token)
):
    """
    生成新聞摘要
    """
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
    summary_data = json.loads(result)
    return {
        "summary": summary_data["影響"],
        "reason": summary_data["原因"]
    }

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """
    提取關鍵字並獲取新聞資料
    """
    prompt = request.prompt
    news_list = []

    # 使用 OpenAI GPT 提取關鍵字
    message_payload = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    try:
        # 與 OpenAI API 交互
        completion = OpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message_payload,
        )
        keywords = completion.choices[0].message.content.strip()

        # 模擬新聞 API 請求
        response = requests.get("https://news-api.example.com", params={"keywords": keywords})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch news data from API")

        news_items = response.json()

        # 處理新聞內容
        for news in news_items:
            try:
                article_response = requests.get(news["titleLink"])
                parsed_article_content = BeautifulSoup(article_response.text, "html.parser")

                # 提取新聞標題和時間
                article_title = parsed_article_content.find("h1", class_="article-content__title").text
                article_time = parsed_article_content.find("time", class_="article-content__time").text

                # 提取文章內容
                content_section = parsed_article_content.find("section", class_="article-content__editor")
                paragraphs = [
                    paragraph.text
                    for paragraph in content_section.find_all("p")
                    if paragraph.text.strip() != "" and "▪" not in paragraph.text
                ]

                # 整合新聞資料
                detailed_news = {
                    "url": news["titleLink"],
                    "title": article_title,
                    "time": article_time,
                    "content": " ".join(paragraphs),
                }
                news_list.append(detailed_news)
            except Exception as e:
                print(f"Error processing news item: {e}")

        # 依時間排序並返回結果
        return sorted(news_list, key=lambda x: x["time"], reverse=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or process news data: {e}")
