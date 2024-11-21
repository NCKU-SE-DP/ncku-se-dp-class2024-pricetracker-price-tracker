import itertools
import requests
from urllib.parse import quote
import json
from bs4 import BeautifulSoup
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from ..database import Session
from .models import NewsArticle
from ..auth.models import user_news_association_table

article_id_counter = itertools.count(start=1000000)
def add_news_article_to_db(news_article_data):
    """
    將新聞文章新增到資料庫
    :param news_article_data: 新聞文章的資訊
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news_article_data["url"],
        title=news_article_data["title"],
        published_time=news_article_data["time"],
        content=" ".join(news_article_data["content"]),  # 將內容列表轉換為字串
        summary=news_article_data["summary"],
        reason_for_inclusion=news_article_data["reason"],
    ))
    session.commit()
    session.close()

def fetch_news_articles(search_keyword: str, is_initial=False) -> list:
    """
    根據搜尋詞獲取新聞文章
    :param search_keyword: 用來搜尋新聞的關鍵字
    :param fetch_multiple_pages: 是否獲取多個頁面的新聞資料
    :return: 包含新聞資料的列表
    """
    all_news_articles = []
    if is_initial:
        page_results = []
        for page_num in range(1, 10):
            request_params = {
                "page": page_num,
                "id": f"search:{quote(search_keyword)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=request_params)
            page_results.append(response.json()["lists"])
        for page_data in page_results:
            all_news_articles.append(page_data)
    else:
        request_params = {
            "page": 1,
            "id": f"search:{quote(search_keyword)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=request_params)
        all_news_articles = response.json()["lists"]
    return all_news_articles

def process_and_store_relevant_news(fetch_multiple_pages=False):
    """
    獲取並處理相關的新聞資料，並將符合條件的新聞存入資料庫
    :param fetch_multiple_pages: 是否需要抓取多頁的新聞
    :return:
    """
    news_articles = fetch_news_articles("價格", is_initial=fetch_multiple_pages)
    for article in news_articles:
        article_title = article["title"]
        relevance_assessment_prompt = [
            {
                "role": "system",
                "content": (
                    "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，"
                    "並給予 'high'、'medium'、'low' 評價。(僅需回答 'high'、'medium'、'low' 三個詞之一)"
                ),
            },
            {"role": "user", "content": f"{article_title}"},
        ]
        ai_response = OpenAI(api_key="xxx").chat.completions.create(
            model="gpt-3.5-turbo",
            messages=relevance_assessment_prompt,
        )
        relevance_rating = ai_response.choices[0].message.content
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
            
            summary_generation_prompt = [
                {
                    "role": "system",
                    "content": (
                        "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 "
                        "(影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"
                    ),
                },
                {"role": "user", "content": " ".join(detailed_article["content"])},
            ]
            
            summary_response = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=summary_generation_prompt,
            )
            
            summary_result = json.loads(summary_response.choices[0].message.content)
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
    # :return: (點贊總數, 當前使用者是否已點贊)
    return total_upvotes, has_voted

def toggle_article_upvote(article_id, user_id, db_session):
    """
    切換用戶對文章的 upvote 狀態：如果用戶已 upvote 該文章則移除 upvote ，否則添加 upvote。
    :param article_id: 欲 upvote 或取消 upvote 的文章 ID。
    :param user_id: 執行 upvote 操作的用戶 ID。
    :param db_session: 資料庫會話，用來執行查詢和操作。
    :return: "Upvote removed" 或 "Article upvoted" 字串，表示操作結果。
    """
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
        db_session.execute(delete_upvote)
        db_session.commit()
        return "Upvote removed"
    else:
        add_upvote = insert(user_news_association_table).values(
            news_articles_id=article_id, user_id=user_id
        )
        db_session.execute(add_upvote)
        db_session.commit()
        return "Article upvoted"