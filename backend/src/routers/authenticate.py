from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..models import User
from ..schemas import UserAuthSchema
from ..database import get_db
from ..service import create_access_token, verify_password
from passlib.context import CryptContext
from ..dependence import authenticate_user_token

router = APIRouter(prefix="/api/v1/users")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=UserAuthSchema)
def register_user(user: UserAuthSchema, db: Session = Depends(get_db)):
    """
    註冊新用戶
    """
    # 檢查用戶名是否已存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # 加密密碼並創建新用戶
    hashed_password = password_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
async def login_for_access_token(form_data: UserAuthSchema, db: Session = Depends(get_db)):
    """
    用戶登入，並獲取訪問令牌
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserAuthSchema)
def get_logged_in_user(current_user: User = Depends(authenticate_user_token)):
    """
    獲取當前已登入的用戶資訊
    """
    return current_user

@router.put("/me", response_model=UserAuthSchema)
def update_user(user_update: UserAuthSchema, db: Session = Depends(get_db), current_user: User = Depends(authenticate_user_token)):
    """
    更新當前用戶的帳號資料，如更改用戶名或密碼
    """
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.username:
        db_user.username = user_update.username
    if user_update.password:
        db_user.hashed_password = password_context.hash(user_update.password)

    db.commit()
    db.refresh(db_user)
    return db_user