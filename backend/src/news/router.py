from fastapi import APIRouter, Depends
import json
from ..database import session_opener
from .schemas import (PromptRequest,NewsSumaryRequestSchema)
from ..auth.service import (
    authenticate_user_token,
    )
from .service import (
    get_article_upvote_details,
    fetch_news_articles_by_keyword,
    article_id_counter,
    toggle_upvote,
    udn_crawler,
    convert_news_to_dict
    
)
import os
from .models import NewsArticle
from openai import OpenAI
from bs4 import BeautifulSoup
import requests
router = APIRouter(
    prefix="/news",
    tags=["News", "v1"]
)

@router.get(path='/news')
def read_news(database=Depends(session_opener)):
    """
    read new

    :param db:
    :return:
    """
    news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for new in news:
        upvotes, upvoted = get_article_upvote_details(new.id, None, database)
        result.append(
            {**new.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
        )
    return result

@router.get(path='/user_news')
def read_user_news(
        database=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """
    read user new

    :param db:
    :param u:
    :return:
    """
    news = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, user.id, database)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return result

@router.post(path='/search_news')
async def search_news(request: PromptRequest):
    prompt = request.prompt
    news_list = []
    keyword_prompt  = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=keyword_prompt ,
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_items = fetch_news_articles_by_keyword(keywords, is_initial=False)
    for news in news_items:
        try:
            detailed_news = convert_news_to_dict(udn_crawler.parse(news.url))
            detailed_news["id"] = next(article_id_counter)
            news_list.append(detailed_news)
        except Exception as error_message:
            print(error_message)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)


@router.post(path='/news_summary')
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}
    summary_prompt = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=summary_prompt ,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

@router.post(path='/{id}/upvote')
def upvote_article(
        id,
        database=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    message = toggle_upvote(id, user.id, database)
    return {"message": message}