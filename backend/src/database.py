
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# 創建資料庫引擎
engine = create_engine(DATABASE_URL, echo=True)

# 創建會話生成器
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 定義基礎模型類
Base = declarative_base()

# 資料庫依賴注入函數
def get_db():
    """
    獲取資料庫會話，用於依賴注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
