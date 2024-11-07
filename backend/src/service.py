import json
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User, NewsArticle, user_news_association_table

# 設定密碼加密上下文
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證用戶輸入的密碼是否與儲存的加密密碼匹配
    """
    return password_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """
    將用戶密碼加密以進行安全存儲
    """
    return password_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    創建 JWT 訪問令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def add_news_to_db(news_data: dict, db: Session):
    """
    將新聞資料添加到資料庫中
    """
    news_article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),
        summary=news_data["summary"],
        reason=news_data["reason"],
    )
    db.add(news_article)
    db.commit()

def fetch_and_store_news(db: Session):
    """
    從外部來源獲取新聞資料並存儲到資料庫中
    """
    # 假設這是從外部 API 獲取新聞資料的模擬函數
    news_data_list = [
        # 例子新聞數據
        {
            "url": "https://example.com/news1",
            "title": "Example News 1",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": ["News content paragraph 1", "paragraph 2"],
            "summary": "Example summary",
            "reason": "Example reason",
        },
        # 更多新聞...
    ]
    for news_data in news_data_list:
        add_news_to_db(news_data, db)

def get_news_article_upvote_details(article_id: int, user_id: int, db: Session) -> tuple:
    """
    獲取特定新聞文章的點贊數及用戶點贊狀態
    """
    # 查詢點贊數
    upvote_count = db.query(user_news_association_table).filter_by(news_article_id=article_id).count()
    
    # 檢查當前用戶是否已點贊該文章
    is_upvoted = db.query(user_news_association_table).filter_by(news_article_id=article_id, user_id=user_id).first() is not None
    
    return upvote_count, is_upvoted

def toggle_news_article_upvote(article_id: int, user_id: int, db: Session) -> str:
    """
    切換新聞文章的點贊狀態（添加或移除點贊）
    """
    # 檢查是否已點贊
    upvote_exists = db.query(user_news_association_table).filter_by(news_article_id=article_id, user_id=user_id).first()
    
    if upvote_exists:
        # 如果已點贊則移除點贊
        db.query(user_news_association_table).filter_by(news_article_id=article_id, user_id=user_id).delete()
        db.commit()
        return "Upvote removed"
    else:
        # 否則添加點贊
        db.execute(user_news_association_table.insert().values(news_article_id=article_id, user_id=user_id))
        db.commit()
        return "Article upvoted"
