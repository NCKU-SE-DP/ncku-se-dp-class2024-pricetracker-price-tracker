from ..database import Base
from ..models import user_news_association_table
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from .constant import MAX_PASSWORD_LENGTH,MAX_USERNAME_LENGTH
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(MAX_USERNAME_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(MAX_PASSWORD_LENGTH), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )
