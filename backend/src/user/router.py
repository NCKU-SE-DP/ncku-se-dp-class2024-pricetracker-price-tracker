from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
    
from ..auth.database import session_opener
from ..auth.utils import check_user_password_is_correct, create_access_token
from ..models import User
from .schemas import UserAuthSchema
from ..auth.database import authenticate_user_token
from ..config import AppConfig
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """
    Get the prices of necessities.

    :param category: The category of the commodity.
    :type category: str, optional
    :param commodity: The name of the commodity.
    :type commodity: str, optional
    :return: JSON response containing the prices of necessities.
    :rtype: dict
    """
    user = check_user_password_is_correct(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=AppConfig.INTERVAL_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """
    Create a new user.

    :param user: The user information.
    :type user: UserAuthSchema
    :param db: The database session.
    :type db: sqlalchemy.orm.Session
    :return: The created user.
    :rtype: User
    """
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    """
    Get the current authenticated user.

    :param user: The authenticated user.
    :type user: User
    :return: A dictionary containing the username of the authenticated user.
    :rtype: dict
    """
    return {"username": user.username}