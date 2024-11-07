from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from .config import JWT_SECRET_KEY
from .database import get_db
from .models import User

# OAuth2 密碼流配置，指定 token 的 URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/authenticate/login")

def authenticate_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    使用 JWT token 進行用戶身份驗證，並從資料庫中獲取用戶資訊。
    """
    try:
        # 解碼 JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: username not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 從資料庫中獲取用戶
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
