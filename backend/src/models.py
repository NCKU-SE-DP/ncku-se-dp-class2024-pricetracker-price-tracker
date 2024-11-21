from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .config import UserConstants

Base = declarative_base()


user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        hashed_password (str): The hashed password of the user.
        upvoted_news (list): The list of news articles upvoted by the user.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(UserConstants.user_max_length), unique=True, nullable=False)
    hashed_password = Column(String(UserConstants.password_max_length), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    """
    Represents a news article in the system.

    Attributes:
        id (int): The unique identifier for the news article.
        url (str): The URL of the news article.
        title (str): The title of the news article.
        time (str): The publication time of the news article.
        content (str): The content of the news article.
        summary (str): The summary of the news article.
        reason (str): The reason or impact of the news article.
        upvoted_by_users (list): The list of users who upvoted the news article.
    """
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )
