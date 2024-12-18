from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..auth.models import User
from .schemas import UserAuthSchema
from ..database import session_opener
from ..auth.service import authenticate_user_token, check_user_password_is_correct, create_access_token, pwd_context
from ..config import Config
from ..logger import logger
from ..exceptions_handler import (
    APIException,
    InternalServerErrorException,
    InvalidUsernameSizeException,
    InvalidPasswordSizeException
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    """
    這個 API 端點返回當前用戶的基本資訊，供已認證的用戶使用。
    :param user: 經由 `authenticate_user_token` 認證的用戶對象。
    :return: JSON 格式的用戶資訊，包括 `username`。
    """
    return {"username": user.username}

@router.post("/login")
async def login_for_access_token(
    user_data: OAuth2PasswordRequestForm = Depends(),
    db_session: Session = Depends(session_opener)
):
    """
    使用者登入並生成訪問令牌 (Access Token)。
    :param form_data: 使用者提交的登入表單數據，包含 `username` 和 `password`。
    :param db_session: 資料庫會話，用於驗證使用者的帳號和密碼。
    :return: JSON 格式的訪問令牌資訊，包括 `access_token` 和 `token_type`。
    """
    try:
        if len(user_data.username) > Config.Auth.MAX_USERNAME_SIZE:
            logger.error(f"User login failed: {InvalidUsernameSizeException(len(user_data.username))}")
            raise InvalidUsernameSizeException(len(user_data.username))
        if len(user_data.password) > Config.Auth.MAX_PASSWORD_SIZE:
            logger.error(f"User login failed: {InvalidPasswordSizeException(len(user_data.username))}")
            raise InvalidPasswordSizeException(len(user_data.password))
        
        # 驗證使用者的帳號和密碼
        user = check_user_password_is_correct(db_session, user_data.username, user_data.password)

        # 創建訪問令牌，30 分鐘有效期
        access_token = create_access_token(
            data={"sub": str(user.username)},
            expires_delta=timedelta(minutes=Config.News.NEWS_FETCH_INTERVAL_TIME)
        )
        logger.info(f"User '{user.username}' logged in successfully")
        return {"access_token": access_token, "token_type": "bearer"}
    except APIException as e:
        logger.error(f"User login failed: {e}")
        raise e
    except Exception as e:
        db_session.rollback()
        logger.error(f"User login failed: {e}")
        raise InternalServerErrorException(e)

@router.post("/register")
def create_user(user_data: UserAuthSchema , db_session: Session = Depends(session_opener)):
    """
    註冊新使用者，將使用者資訊儲存到資料庫中。
    :param user_data: 使用者註冊信息，包含 `username` 和 `password`。
    :param db_session: 資料庫會話，用於將新使用者添加到資料庫。
    :return: 新增的 `User` 對象，包含使用者的基本資訊。
    """
    try:
        if len(user_data.username) > Config.Auth.MAX_USERNAME_SIZE:
            logger.error(f"User login failed: {InvalidUsernameSizeException(len(user_data.username))}")
            raise InvalidUsernameSizeException(len(user_data.username))
        if len(user_data.password) > Config.Auth.MAX_PASSWORD_SIZE:
            logger.error(f"User login failed: {InvalidPasswordSizeException(len(user_data.username))}")
            raise InvalidPasswordSizeException(len(user_data.password))
        
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(username=user_data.username, hashed_password=hashed_password)
        
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        return new_user
    except APIException as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=400, detail=str(e))