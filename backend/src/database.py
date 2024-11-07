from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, ForeignKey

Base = declarative_base()

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

engine = create_engine("sqlite:///news_database.db", echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def session_opener():
    """
    創建並管理資料庫會話，確保在操作完成後自動關閉會話。
    :yield: 生成一個資料庫會話 (Session) 供依賴注入使用。
    """
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()