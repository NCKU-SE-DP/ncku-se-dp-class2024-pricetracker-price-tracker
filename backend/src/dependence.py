from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from .config import JWT_SECRET_KEY
from .database import get_db
from .models import User

# OAuth2 密碼流配置，指定 token 的 URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/authenticate/login")

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(get_db)):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return db.query(User).filter(User.username == payload.get("sub")).first()
