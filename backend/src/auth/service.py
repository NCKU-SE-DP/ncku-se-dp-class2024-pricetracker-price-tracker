from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
from jose import JWTError, jwt
from .models import User
from .config import get_auth_settings
from ..database import session_opener
from datetime import datetime, timedelta
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
auth_settings=get_auth_settings()
def verify(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


def check_user_password_is_correct(database, name, pwd):
    user = database.query(User).filter(User.username == name).first()
    if not verify(pwd, user.hashed_password):
        return False
    return user


def authenticate_user_token(
    token = Depends(oauth2_scheme),
    database = Depends(session_opener)
):
    payload = jwt.decode(token, auth_settings.ACCESS_TOKEN_SECRET_KEY, algorithms=[auth_settings.ACCESS_TOKEN_ALGORITHM])
    return database.query(User).filter(User.username == payload.get("sub")).first()


def create_access_token(data, expires_delta=None):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_json_webtoken = jwt.encode(to_encode, auth_settings.ACCESS_TOKEN_SECRET_KEY, algorithm=auth_settings.ACCESS_TOKEN_ALGORITHM)
    return encoded_json_webtoken