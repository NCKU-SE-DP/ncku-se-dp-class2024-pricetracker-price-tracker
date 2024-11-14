from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..models import User
from ..schemas import UserAuthSchema
from ..database import get_db
from ..service import create_access_token, verify_password
from passlib.context import CryptContext
from ..dependence import authenticate_user_token
from datetime import timedelta

router = APIRouter(prefix="/api/v1/users")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
def register_user(user: UserAuthSchema, db: Session = Depends(get_db)):
    """create user"""
    hashed_password = password_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """login"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserAuthSchema)
def get_logged_in_user(current_user: User = Depends(authenticate_user_token)):
    """
    獲取當前已登入的用戶資訊
    """
    return {"username": current_user.username, "password": current_user.hashed_password}

@router.put("/me", response_model=UserAuthSchema)
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}