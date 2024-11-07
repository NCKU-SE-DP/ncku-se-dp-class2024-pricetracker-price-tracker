from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import session_opener
from .schemas import UserAuthSchema
from ..auth.service import (check_user_password_is_correct,create_access_token,pwd_context,authenticate_user_token)
from ..auth.models import User
router = APIRouter(
    prefix='/users',
    tags=["Users", "v1"],
)

@router.post(path='/login')
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(session_opener)
):
    """login"""
    user = check_user_password_is_correct(database, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(path='/register')
def create_user(user: UserAuthSchema, database: Session = Depends(session_opener)):
    """create user"""
    hashed_password = pwd_context.hash(user.password)
    database_user = User(username=user.username, hashed_password=hashed_password)
    database.add(database_user)
    database.commit()
    database.refresh(database_user)
    return database_user

@router.get(path='/me')
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}