from datetime import datetime
import json
import itertools
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing import List, Optional

from models import NewsArticle, user_news_association_table, User
from database import get_db
from auth.auth import get_current_user
from config import settings
from crawler import udn_crawler
import llm_client.openai_client as openai_client
ai_client = openai_client.create_openai_client(settings.OPENAI_API_KEY)
router = APIRouter(prefix="/api/v1/news", tags=["news"])
_id_counter = itertools.count(start=1000000)

class NewsResponse(BaseModel):
    id: int
    url: str
    title: str
    time: str
    content: str
    summary: Optional[str]
    reason: Optional[str]
    upvotes: int
    is_upvoted: bool

class PromptRequest(BaseModel):
    prompt: str

class NewsSummaryRequest(BaseModel):
    content: str

async def get_new(db: Session, is_initial: bool = False):
    
    """定期獲取新聞"""
    try:
        if is_initial:
            news_data = get_new_info("價格", is_initial=True)
        else:
            news_data = get_new_info("價格", is_initial=False)
        
        for news in news_data:
            print(news)
            try:
                title = news["title"]
                relevance_response = await ai_client.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
                        },
                        {
                            "role": "user",
                            "content": title
                        }
                    ]
                )
                
                if isinstance(relevance_response, dict):
                    relevance = relevance_response.get('content', '').lower().strip()
                else:
                    relevance = str(relevance_response).lower().strip()
                
                if relevance == "high":
                    try:
                        article_content = udn_crawler.get_article_content(news["titleLink"])
                        if article_content:
                            summary_result = await ai_client.chat_completion(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
                                    },
                                    {
                                        "role": "user",
                                        "content": article_content["content"]
                                    }
                                ]
                            )
                            
                            try:
                                if isinstance(summary_result, dict):
                                    summary_text = summary_result.get('content', '{}')
                                else:
                                    summary_text = str(summary_result)
                                    
                                summary_dict = json.loads(summary_text)
                                article_content["summary"] = summary_dict["影響"]
                                article_content["reason"] = summary_dict["原因"]
                                add_new_article(article_content, db)
                            except json.JSONDecodeError:
                                print(f"Failed to parse summary JSON for article: {title}")
                                continue
                    except Exception as e:
                        print(f"Failed to get article content for {title}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error processing news item: {str(e)}")
                continue
    except Exception as e:
        print(f"Error in get_new: {str(e)}")

def get_new_info(search_term: str, is_initial: bool = False):
    """從UDN獲取新聞列表"""
    return udn_crawler.get_news_list(search_term, is_initial)

def add_new_article(news_data: dict, db: Session):
    """添加新聞到資料庫"""
    article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=news_data["content"],
        summary=news_data.get("summary"),
        reason=news_data.get("reason"),
    )
    db.add(article)
    db.commit()
    return article

def get_article_upvote_details(article_id: int, user_id: Optional[int], db: Session):
    """獲取文章的投票詳情"""
    count = db.query(user_news_association_table).filter_by(news_articles_id=article_id).count()
    voted = False
    if user_id:
        voted = (
            db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id, user_id=user_id)
            .first() is not None
        )
    return count, voted

@router.get("/news", response_model=List[NewsResponse])
def read_news(db: Session = Depends(get_db)):
    """獲取所有新聞"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, None, db)
        article_dict = {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": upvoted
        }
        result.append(article_dict)
    return result

@router.get("/user_news", response_model=List[NewsResponse])
def read_user_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取用戶相關的新聞"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, current_user.id, db)
        article_dict = {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": upvoted
        }
        result.append(article_dict)
    return result
@router.post("/search_news")
async def search_news(
    request: PromptRequest,
    db: Session = Depends(get_db)
):
    """搜尋新聞"""
    response = await ai_client.chat_completion(
        messages=[
            {
                "role": "system", 
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，且只需一個關鍵字)",
            },
            {
                "role": "user",
                "content": request.prompt
            }
        ]
    )
    keywords = response["content"]
    
    news_list = []
    news_items = udn_crawler.get_news_list(str(keywords), is_initial=False)
    
    for news in news_items:
        try:
            article_content = udn_crawler.get_article_content(news["titleLink"])
            if article_content:
                article_content["id"] = next(_id_counter)
                news_list.append(article_content)
        except Exception as e:
            continue
            
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary")
async def news_summary(
    request: NewsSummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """生成新聞摘要"""
    result = await ai_client.chat_completion(
        messages=[
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
            },
            {
                "role": "user",
                "content": request.content
            }
        ]
    )
    
    try:
        summary_dict = json.loads(result.get("content", "{}"))
        return {
            "summary": summary_dict["影響"],
            "reason": summary_dict["原因"]
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to generate summary")

@router.post("/{id}/upvote")
def upvote_article(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """投票/取消投票文章"""
    article = db.query(NewsArticle).filter(NewsArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == id,
            user_news_association_table.c.user_id == current_user.id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == id,
            user_news_association_table.c.user_id == current_user.id,
        )
        db.execute(delete_stmt)
        db.commit()
        return {"message": "Upvote removed"}
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=id,
            user_id=current_user.id
        )
        db.execute(insert_stmt)
        db.commit()
        return {"message": "Article upvoted"} 