import json
from .models import NewsArticle
from urllib.parse import quote
import requests
from .constant import NEWS_LINK
import os
from openai import OpenAI
from bs4 import BeautifulSoup
import itertools
from ..models import user_news_association_table
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from src.news.config import get_NewsSettings
from src.crawler.udn_crawler import UDNCrawler
from src.llm_client.openai_client import LLMClient
llm_client=LLMClient()
udn_crawler = UDNCrawler()
NewsSettings=get_NewsSettings()
article_id_counter = itertools.count(start=1000000)
openai_client = OpenAI(api_key=NewsSettings.Openai_APIKEY)
def process_news_item(news):
    """
    Fetches detailed content from a news article.
    """
    return udn_crawler.parse(news.url)
def convert_news_to_dict(news):
    return {
        "url": news.url,
        "title": news.title,
        "time": news.time,
        "content": news.content,
    }
def add_news_article(news_data):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    udn_crawler.save(news=news_data, db=session)

def fetch_news_articles_by_keyword(search_term, is_initial=False):
    """
    get new by keyword

    :param search_term: keyword
    :param is_initial: bool indicate whether  this is the initial fetch
    :return:
    """
    if is_initial:
        return udn_crawler.startup(search_term=search_term)
    else:
        return udn_crawler.get_headline(search_term=search_term, page=1)
def get_new_info(is_initial=False):
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = fetch_news_articles_by_keyword("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        summary_prompt = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{title}"},
        ]
        summary_completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=summary_prompt,
        )
        relevance = llm_client.evaluate_relevance(title, "民生用品的價格變化")
        if relevance == "high":
            detailed_news = udn_crawler.parse(news.url)

            result = llm_client.generate_summary(" ".join(detailed_news["content"]))

            detailed_news["summary"] = result["影響"]
            detailed_news["reason"] = result["原因"]
            
            add_news_article(detailed_news)

def get_article_upvote_details(article_id, uid, database):
    counter = (
        database.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    voted = False
    if uid:
        voted = (
                database.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=uid)
                .first()
                is not None
        )
    return counter, voted
def toggle_upvote(article_id, user_id, database):
    existing_upvote = database.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == article_id,
            user_news_association_table.c.user_id == user_id,
        )
        database.execute(delete_stmt)
        database.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=article_id, user_id=user_id
        )
        database.execute(insert_stmt)
        database.commit()
        return "Article upvoted"


def news_exists(id2, database: Session):
    return database.query(NewsArticle).filter_by(id=id2).first() is not None