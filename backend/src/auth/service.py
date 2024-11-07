from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from ..database import session_opener
from ..config import Config
from .models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Config.Auth.TOKEN_URL)

def verify(plain_password, hashed_password):
    """
    驗證密碼是否正確。
    :param plain_password: 待驗證的密碼（通常為使用者輸入的明文密碼）。
    :param hashed_password: 加密後的密碼（通常從數據庫中提取的哈希密碼）。
    :return: 如果 `plain_password` 與 `hashed_password` 相符，返回 True；否則返回 False。
    """
    return pwd_context.verify(plain_password, hashed_password)

def check_user_password_is_correct(db_session, username, input_password):
    """
    檢查使用者的密碼是否正確
    :param db_session: 資料庫的 session
    :param username: 使用者的名稱
    :param input_password: 輸入的密碼
    :return: 如果密碼正確，返回使用者物件；否則返回 False
    """
    user = db_session.query(User).filter(User.username == username).first()
    if not verify(input_password, user.hashed_password):
        return False
    return user

def authenticate_user_token(
    token: str = Depends(oauth2_scheme),
    db_session = Depends(session_opener)
):
    """
    根據 JWT token 認證使用者
    :param token: 用於認證的 JWT token
    :param db_session: 資料庫的 session
    :return: 對應於 token 的使用者，如果找不到則返回 None
    """
    token_payload = jwt.decode(token, Config.Auth.SECRET_KEY, algorithms=[Config.Auth.HASHED_METHOD])
    
    # 根據 token payload 中的 "sub" 字段（通常是 username）查找使用者
    return db_session.query(User).filter(User.username == token_payload.get("sub")).first()

def create_access_token(data, expires_delta=None):
    """
    創建一個加密的 JWT（JSON Web Token），用於用戶認證。
    :param data (dict): 要編碼進 token 的數據，通常包含用戶相關資訊。
    :param expires_delta (timedelta, optional): Token 的過期時間增量。如果未提供，將使用預設的過期時間。
    :return: 編碼後的 JWT 字串。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Config.Auth.TOKEN_EXPIRE_TIME)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, Config.Auth.SECRET_KEY, algorithm=Config.Auth.HASHED_METHOD)
    return encoded_jwt