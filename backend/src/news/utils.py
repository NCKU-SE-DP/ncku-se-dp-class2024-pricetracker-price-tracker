from urllib.parse import quote
import requests
import json
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from src.models import user_news_association_table, NewsArticle
from openai import OpenAI
from src.auth.database import SessionLocal

def store_news(news_data):
    """
    Add a news article to the database.

    :param news_data: Dictionary containing news information with keys 'url', 'title', 'time', 'content', 'summary', and 'reason'.
    :type news_data: dict
    :return: None
    """
    session = SessionLocal()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()
    
def get_new_info(search_term, fetch_all_pages=False):
    """
    Fetch new information based on a search term.

    :param search_term: The term to search for.
    :type search_term: str
    :param fetch_all_pages: Whether to fetch all pages of results or just the first page, defaults to False.
    :type fetch_all_pages: bool, optional
    :return: List of dictionaries containing news information.
    :rtype: list
    """
    news_data = []
    # iterate pages to get more news data, not actually get all news data
    if fetch_all_pages:
        data_pages = []
        for page_number in range(1, 10):
            paged_params = {
                "page": page_number,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=paged_params)
            data_pages.append(response.json()["lists"])

        for page in data_pages:
            news_data.extend(page)
    else:
        params = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=params)

        news_data = response.json()["lists"]
    return news_data


def toggle_upvote(n_id, u_id, db):
    """
    Toggle the upvote status of a news article for a user.

    :param n_id: The ID of the news article.
    :type n_id: int
    :param u_id: The ID of the user.
    :type u_id: int
    :param db: The database session.
    :type db: sqlalchemy.orm.Session
    :return: A message indicating whether the upvote was added or removed.
    :rtype: str
    """
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == n_id,
            user_news_association_table.c.user_id == u_id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == n_id,
            user_news_association_table.c.user_id == u_id,
        )
        db.execute(delete_stmt)
        db.commit()
        return "Upvote removed"
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=n_id, user_id=u_id
        )
        db.execute(insert_stmt)
        db.commit()
        return "Article upvoted"

def get_new(fetch_all_pages=False):
    """
    Fetch new information.

    :param fetch_all_pages: Whether to fetch all pages of results or just the first page, defaults to False.
    :type fetch_all_pages: bool, optional
    :return: List of dictionaries containing news information.
    :rtype: list
    """
    news_data = get_new_info("價格", fetch_all_pages=fetch_all_pages)
    for news in news_data:
        news_title = news["title"]
        messages = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{news_title}"},
        ]
        ai_response = OpenAI(api_key="xxx").chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        relevance = ai_response.choices[0].message.content

        if relevance == "high":
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            news_title = soup.find("h1", class_="article-content__title").text
            news_time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = soup.find("section", class_="article-content__editor")

            paragraphs = [
                paragraphs.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news =  {
                "url": news["titleLink"],
                "title": news_title,
                "time": news_time,
                "content": paragraphs,
            }
            summary_messages = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(detailed_news["content"])},
            ]

            completion = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=summary_messages,
            )
            result = completion.choices[0].message.content
            result = json.loads(result)
            detailed_news["summary"] = result["影響"]
            detailed_news["reason"] = result["原因"]
            store_news(detailed_news)

def get_article_upvote_details(article_id, uid, db):
    """
    Get the upvote details for a news article.

    :param article_id: The ID of the news article.
    :type article_id: int
    :param uid: The ID of the user (optional).
    :type uid: int or None
    :param db: The database session.
    :type db: sqlalchemy.orm.Session
    :return: A tuple containing the upvote count and whether the user has upvoted the article.
    :rtype: tuple
    """
    upvote_count = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=article_id)
        .count()
    )
    user_voted = False
    if uid:
        user_voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=uid)
                .first()
                is not None
        )
    return upvote_count, user_voted

def news_exists(id2, db: Session):
    """
    Check if a news article exists in the database.

    :param id2: The ID of the news article.
    :type id2: int
    :param db: The database session.
    :type db: sqlalchemy.orm.Session
    :return: True if the news article exists, False otherwise.
    :rtype: bool
    """
    return db.query(NewsArticle).filter_by(id=id2).first() is not None

def generate_ai_response(content, prompt):
    message = [
        {
            "role": "system",
            "content": prompt,
        },
        {"role": "user", "content": f"{content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message,
    )
    return completion.choices[0].message.content