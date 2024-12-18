import itertools
import requests
import json
from bs4 import BeautifulSoup
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from sqlalchemy.exc import SQLAlchemyError
from ..exceptions_handler import (
    ArticleNotFoundException,
    InternalServerErrorException
)
from .models import NewsArticle
from ..logger import logger
from ..auth.models import user_news_association_table
from ..crawler.udn_crawler import UDNCrawler
from ..crawler.crawler_base import NewsWithSummary
from ..llm_client.clients import OpenAIClient, AnthropicClient
from dotenv import load_dotenv
import os
load_dotenv()
openai_client = OpenAIClient(api_key=os.getenv("openai"))
anthropic_client = AnthropicClient(api_key=os.getenv("claude"))

crawler = UDNCrawler()

def parse_summary_result():
    response_data = {}
    if result:
        try:
            result = json.loads(result)
            response_data["summary"] = result["影響"]
            response_data["reason"] = result["原因"]
        except json.JSONDecodeError:
            return response_data
    return response_data
    
def process_news_item(news):
    return crawler.validate_and_parse(news.url)

def convert_news_to_dict(news):
    return {
        "url": news.url,
        "title": news.title,
        "time": news.time,
        "content": news.content,
    }

article_id_counter = itertools.count(start=1000000)
def add_news_article_to_db(news_article_data):
    """
    將新聞文章新增到資料庫
    :param news_article_data: 新聞文章的資訊
    :return:
    """
    session = Session()
    crawler.save(
        news=NewsWithSummary(summary=news_article_data["summary"], reason=news_article_data["reason"]),
        db=session
    )

def fetch_news_with_details(db: Session, user_id: Optional[int] = None) -> list:
    """
    Fetch all news articles with their upvote details.
    :param db: Database session dependency for querying news articles.
    :param user_id: Optional user ID to fetch user-specific upvote status.
    :return: A list of news articles with upvote count and user-specific upvote status.
    """
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except SQLAlchemyError as e:
        logger.error("Failed to fetch news articles from database", exc_info=True)
        raise InternalServerErrorException(e)

    result = []
    for article in news:
        try:
            upvotes, upvoted = get_article_upvote_details(article.id, user_id, db)
            result.append(
                {
                    **article.__dict__,
                    "upvotes": upvotes,
                    "is_upvoted": upvoted,
                }
            )
        except Exception as e:
            logger.error(f"Failed to fetch upvote details for article ID: {article.id}", exc_info=True)
    return result

def fetch_news_articles(search_keyword: str, is_initial=False) -> list:
    """
    根據搜尋詞獲取新聞文章
    :param search_keyword: 用來搜尋新聞的關鍵字
    :param fetch_multiple_pages: 是否獲取多個頁面的新聞資料
    :return: 包含新聞資料的列表
    """
    
    if is_initial:
        return crawler.startup(search_keyword)
    else:
        return crawler.get_headline(search_keyword, 1)

def process_and_store_relevant_news(fetch_multiple_pages=False):
    """
    獲取並處理相關的新聞資料，並將符合條件的新聞存入資料庫
    :param fetch_multiple_pages: 是否需要抓取多頁的新聞
    :return:
    """
    news_articles = fetch_news_articles("價格", is_initial=fetch_multiple_pages)
    for article in news_articles:
        article_title = article["title"]
        relevance_rating = openai_client.evaluate_relevance(article_title)
        if relevance_rating == "high":
            article_response = requests.get(article["titleLink"])
            article_soup = BeautifulSoup(article_response.text, "html.parser")
            
            article_title = article_soup.find("h1", class_="article-content__title").text
            publication_time = article_soup.find("time", class_="article-content__time").text
            
            content_section = article_soup.find("section", class_="article-content__editor")
            article_paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            
            detailed_article = {
                "url": article["titleLink"],
                "title": article_title,
                "time": publication_time,
                "content": article_paragraphs,
            }
            summary_result = openai_client.generate_summary(" ".join(detailed_article["content"]))
            detailed_article["summary"] = summary_result["影響"]
            detailed_article["reason"] = summary_result["原因"]
            
            add_news_article_to_db(detailed_article)

def get_article_upvote_details(article_id, user_id, db_session):
    """
    獲取新聞文章的點贊詳情
    :param article_id: 文章的 ID
    :param user_id: 使用者的 ID (可選)
    :param db_session: 資料庫的 session
    :return: (點贊總數, 當前使用者是否已點贊)
    """
    try:
        if not news_exists(article_id, db_session):
            logger.error(f"Failed to process article ID: {article_id}")
            raise ArticleNotFoundException()
        total_upvotes = (
            db_session.query(user_news_association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )
        has_voted = False
        if user_id:
            has_voted = (
                db_session.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
            )
        logger.info(f"Successfully fetched upvote count for article ID: {article_id}")
        return total_upvotes, has_voted # :return: (點贊總數, 當前使用者是否已點贊)
    except Exception as e:
        logger.error(f"Failed to fetch upvote count for article ID: {article_id}", exc_info=True)
        raise InternalServerErrorException(e)

def toggle_article_upvote(article_id, user_id, db_session):
    """
    切換用戶對文章的 upvote 狀態：如果用戶已 upvote 該文章則移除 upvote ，否則添加 upvote。
    :param article_id: 欲 upvote 或取消 upvote 的文章 ID。
    :param user_id: 執行 upvote 操作的用戶 ID。
    :param db_session: 資料庫會話，用來執行查詢和操作。
    :return: "Upvote removed" 或 "Article upvoted" 字串，表示操作結果。
    """
    try:
        if not news_exists(article_id, db_session):
            logger.error(f"Failed to process article ID: {article_id}")
            raise ArticleNotFoundException()
        existing_upvote_record = db_session.execute(
            select(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
        ).scalar()

        if existing_upvote_record:
            delete_upvote = delete(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
            logger.info(f"Upvote removed for article ID: {article_id}")
            db_session.execute(delete_upvote)
            db_session.commit()
            return "Upvote removed"
        else:
            add_upvote = insert(user_news_association_table).values(
                news_articles_id=article_id, user_id=user_id
            )
            logger.info(f"Upvote added for article ID: {article_id}")
            db_session.execute(add_upvote)
            db_session.commit()
            return "Article upvoted"

    except Exception as e:
        logger.error(f"Failed to toggle upvote for article ID: {article_id} and user ID: {user_id}", exc_info=True)
        raise InternalServerErrorException(e)

def news_exists(article_id, db: Session):
    try:
        exists = db.query(NewsArticle).filter_by(id=article_id).first()
        if not exists:
            logger.warning(f"Article not found for ID: {article_id}")
        return exists
    except SQLAlchemyError as e:
        logger.error(f"Error processing article ID: {article_id}", exc_info=True)
        raise InternalServerErrorException(e)