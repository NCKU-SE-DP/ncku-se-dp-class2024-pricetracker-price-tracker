import json
import requests
from fastapi import APIRouter, Depends
from openai import OpenAI
from ..auth.service import authenticate_user_token
from ..database import session_opener
from ..logger import logger
from ..exceptions_handler import NoResourceFoundException
from .schemas import PromptRequest, NewsSumaryRequestSchema, NewsSummaryCustomModelRequestSchema
from .service import (
    openai_client,
    anthropic_client,
    article_id_counter,
    fetch_news_articles,
    toggle_article_upvote,
    process_news_item,
    convert_news_to_dict,
    fetch_news_with_details
)
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
    return fetch_news_with_details(db_session, user_id=user.id)

@router.get("/news")
def read_news(db_session=Depends(session_opener)):
    """
    獲取最新的新聞文章
    :param db_session: 資料庫的 session
    :return: 包含新聞文章及其點贊詳情的列表
    """
    return fetch_news_with_details(db_session)

@router.post("/search_news")
async def search_news(request: PromptRequest):
    """
    這個 API 端點根據使用者輸入的新聞描述文字，提取關鍵字並檢索相關新聞，返回包含新聞詳細資訊的列表。
    :param request: `PromptRequest` 類型的請求對象，包含使用者輸入的新聞描述文字 (prompt)。
    :return: JSON 格式的新聞列表，每項新聞包括 `url`、`title`、`time`、`content` 和 `id`。
    """
    user_prompt = request.prompt
    extracted_keywords = openai_client.extract_search(user_prompt)
    # 根據提取的關鍵字獲取新聞文章
    extracted_news_list = []
    relevant_news_items = fetch_news_articles(extracted_keywords, is_initial=False)
    for news_item in relevant_news_items:
        try:
            detailed_news_info = convert_news_to_dict(process_news_item(news_item))
            detailed_news_info["id"] = next(article_id_counter)
            extracted_news_list.append(detailed_news_info)
            logger.info(f"Search news success: {detailed_news_info['title']}")
        except Exception as error:
            logger.error(f"Search news failed: {news_item.url}", error=error)
    if len(extracted_news_list) == 0:
        raise NoResourceFoundException()
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
    result_data = openai_client.generate_summary(news_summary_request.content)
    summary_response["summary"] = result_data["影響"]
    summary_response["reason"] = result_data["原因"]
    return summary_response

@router.post("/news_summary_custom_model")
async def summarize_news_with_custom_model(schema: NewsSummaryCustomModelRequestSchema, user=Depends(authenticate_user_token)):
    response = {}
    if not schema.ai_model:
        return {"message": "Model is required."}
    elif schema.ai_model.lower() == "openai":
        result = openai_client.generate_summary(schema.content)
    elif schema.ai_model.lower() == "anthropic" or schema.ai_model.lower() == "claude":
        result = anthropic_client.generate_summary(schema.content)
    else:
        return {"message": "Invalid model."}
    if result:
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

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
    try:
        upvote_status_message = toggle_article_upvote(article_id, user.id, db_session)
        return {"message": upvote_status_message}
    except Exception as e:
        logger.error(f"Toggle article failed for article ID: {article_id} and user ID: {user.id}", error=e)
        raise NoResourceFoundException()