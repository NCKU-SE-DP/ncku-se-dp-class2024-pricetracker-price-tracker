from fastapi import APIRouter, Depends
import json
from openai import OpenAI
from bs4 import BeautifulSoup
import requests
import itertools

from .schemas import NewsSumaryRequestSchema, PromptRequest
from .utils import get_new_info, toggle_upvote, get_article_upvote_details
from ..auth.database import session_opener, authenticate_user_token
from ..models import NewsArticle

_id_counter = itertools.count(start=1000000)

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/user_news"
)
def read_user_news(
        db=Depends(session_opener),
        u=Depends(authenticate_user_token)
):
    """
    read user new

    :param db: Database session
    :param u: Authenticated user
    :return: List of news articles with their upvote status
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, u.id, db)
        result.append(
            {
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
            }
        )
    return result

@router.post("/search_news")
async def search_news(request: PromptRequest):
    prompt = request.prompt
    news_list = []
    keyword_extraction_prompt = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=keyword_extraction_prompt,
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_articles = get_new_info(keywords, fetch_all_pages=False)
    for news in news_articles:
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = soup.find("section", class_="article-content__editor")

            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            parsed_news = {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            parsed_news["content"] = " ".join(parsed_news["content"])
            parsed_news["id"] = next(_id_counter)
            news_list.append(parsed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)


@router.post("/news_summary")
async def news_summary(
        payload: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}
    request_message = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=request_message,
    )
    result = completion.choices[0].message.content
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

@router.post("/{id}/upvote")
def upvote_article(
        id,
        db=Depends(session_opener),
        u=Depends(authenticate_user_token),
):
    """
    Upvote an article

    :param id: Article ID
    :param db: Database session
    :param u: Authenticated user
    :return: Dictionary containing the operation message
    """
    message = toggle_upvote(id, u.id, db)
    return {"message": message}

@router.get("/news")
def read_news(db=Depends(session_opener)):
    """
    Read news

    :param db: Database session
    :return: List of news articles with their upvote status
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for n in news:
        upvotes, upvoted = get_article_upvote_details(n.id, None, db)
        result.append(
            {**n.__dict__, "upvotes": upvotes, "is_upvoted": upvoted}
        )
    return result

