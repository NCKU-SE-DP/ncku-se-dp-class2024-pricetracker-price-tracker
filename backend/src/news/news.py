from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
from openai import OpenAI
import json
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from ...models import NewsArticle, user_news_association_table
from ...config import settings

_id_counter = itertools.count(start=1000000)

def get_new_info(search_term: str, is_initial: bool = False):
    all_news_data = []
    if is_initial:
        for p in range(1, 10):
            params = {
                "page": p,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=params)
            all_news_data.extend(response.json()["lists"])
    else:
        params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=params)
        all_news_data = response.json()["lists"]
    return all_news_data

def process_news_content(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1", class_="article-content__title").text
    time = soup.find("time", class_="article-content__time").text
    content_section = soup.find("section", class_="article-content__editor")
    paragraphs = [
        p.text
        for p in content_section.find_all("p")
        if p.text.strip() != "" and "▪" not in p.text
    ]
    return title, time, paragraphs

def generate_ai_response(content: str, system_prompt: str):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return completion.choices[0].message.content

def add_new_article(news_data: dict, db: Session):
    article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),
        summary=news_data["summary"],
        reason=news_data["reason"],
    )
    db.add(article)
    db.commit()
    return article

def get_article_upvote_details(article_id: int, user_id: int, db: Session):
    count = db.query(user_news_association_table).filter_by(news_articles_id=article_id).count()
    voted = False
    if user_id:
        voted = (
            db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id, user_id=user_id)
            .first() is not None
        )
    return count, voted

def toggle_upvote(article_id: int, user_id: int, db: Session):
    existing_upvote = db.execute(
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
        db.execute(delete_stmt)
        db.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=article_id, user_id=user_id
        )
        db.execute(insert_stmt)
        db.commit()
        return "Article upvoted" 