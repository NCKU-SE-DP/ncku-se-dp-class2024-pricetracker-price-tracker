import json
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from openai import OpenAI
from ..auth.service import authenticate_user_token
from ..database import session_opener
from .models import NewsArticle
from .schemas import PromptRequest, NewsSumaryRequestSchema
from .service import article_id_counter, fetch_news_articles, get_article_upvote_details, toggle_article_upvote

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.get("/user_news")
def read_user_news(
    db_session=Depends(session_opener),
    user=Depends(authenticate_user_token)
):
    """
    為使用者取得新聞文章，包含點讚詳情。
    :param db_session: 資料庫會話 session 依賴
    :param user: 從 token 獲得的已驗證使用者
    :return: 包含點讚詳情的新聞文章列表
    """
    news_articles = db_session.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    articles_with_upvotes = []

    for article in news_articles:
        upvote_count, is_user_upvoted = get_article_upvote_details(article.id, user.id, db_session)
        articles_with_upvotes.append(
            {
                **article.__dict__,
                "upvotes": upvote_count,
                "is_upvoted": is_user_upvoted,
            }
        )
    return articles_with_upvotes

@router.get("/news")
def read_news(db_session=Depends(session_opener)):
    """
    獲取最新的新聞文章
    :param db_session: 資料庫的 session
    :return: 包含新聞文章及其點贊詳情的列表
    """
    # 將文章按時間倒序排列
    news_articles = db_session.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    
    # 構建返回的結果集，包含每篇文章的點贊數和是否已點贊
    result = []
    for article in news_articles:
        upvotes, is_upvoted = get_article_upvote_details(article.id, None, db_session)
        result.append(
            {**article.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return result

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """
    這個 API 端點根據使用者輸入的新聞描述文字，提取關鍵字並檢索相關新聞，返回包含新聞詳細資訊的列表。
    :param request: `PromptRequest` 類型的請求對象，包含使用者輸入的新聞描述文字 (prompt)。
    :return: JSON 格式的新聞列表，每項新聞包括 `url`、`title`、`time`、`content` 和 `id`。
    """
    user_prompt = request.prompt
    extracted_news_list = []
    prompt_messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{user_prompt}"},
    ]
    ai_completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt_messages,
    )
    extracted_keywords = ai_completion.choices[0].message.content
    
    # 根據提取的關鍵字獲取新聞文章
    relevant_news_items = fetch_news_articles(extracted_keywords, is_initial=False)
    for news_item in relevant_news_items:
        try:
            news_response = requests.get(news_item["titleLink"])
            news_soup = BeautifulSoup(news_response.text, "html.parser")
            news_title = news_soup.find("h1", class_="article-content__title").text
            news_time = news_soup.find("time", class_="article-content__time").text
            news_content_section = news_soup.find("section", class_="article-content__editor")
            content_paragraphs = [
                paragraph.text
                for paragraph in news_content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news_info = {
                "url": news_item["titleLink"],
                "title": news_title,
                "time": news_time,
                "content": content_paragraphs,
            }
            detailed_news_info["content"] = " ".join(detailed_news_info["content"])
            detailed_news_info["id"] = next(article_id_counter)
            extracted_news_list.append(detailed_news_info)
        except Exception as error:
            print(error)
    return sorted(extracted_news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary")
async def news_summary(
    news_summary_request: NewsSumaryRequestSchema, user=Depends(authenticate_user_token)
):
    """
    這個 API 端點接收新聞內容，並生成一個包含新聞影響和原因的摘要。
    :param news_summary_request: 包含新聞內容的請求數據。
    :param user: 經由 `authenticate_user_token` 認證的使用者。
    :return: JSON 格式的摘要結果，包括 `summary` (影響) 和 `reason` (原因)。
    """
    summary_response = {}
    prompt_messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{news_summary_request.content}"},
    ]
    completion_response = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt_messages,
    )

    completion_content = completion_response.choices[0].message.content
    if completion_content:
        result_data = json.loads(completion_content)
        summary_response["summary"] = result_data["影響"]
        summary_response["reason"] = result_data["原因"]
    return summary_response

@router.post("/{article_id}/upvote")
def upvote_article(
    article_id,
    db_session=Depends(session_opener),
    user=Depends(authenticate_user_token),
):
    """
    這個 API 端點處理文章的點讚功能，並返回點讚操作的結果訊息。
    :param article_id: 需要點讚或取消點讚的文章 ID。
    :param db_session: 資料庫會話，用於執行資料庫操作，預設依賴於 `session_opener` 函數。
    :param user: 經由 `authenticate_user_token` 認證的使用者。
    :return: JSON 格式的點讚操作狀態訊息，例如 {"message": "Upvoted"} 或 {"message": "Upvote removed"}。
    """
    upvote_status_message = toggle_article_upvote(article_id, user.id, db_session)
    return {"message": upvote_status_message}