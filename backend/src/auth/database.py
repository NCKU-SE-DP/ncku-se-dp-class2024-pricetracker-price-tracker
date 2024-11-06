from sqlalchemy.orm import Session
from fastapi import Depends
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import  create_engine

from src.models import User, Base

engine = create_engine("sqlite:///news_database.db", echo=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
Base.metadata.create_all(engine)


def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(session_opener)
):
    payload = jwt.decode(token, '1892dhianiandowqd0n', algorithms=["HS256"])
    return db.query(User).filter(User.username == payload.get("sub")).first()