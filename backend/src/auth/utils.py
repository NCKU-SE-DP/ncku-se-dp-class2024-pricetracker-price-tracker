from passlib.context import CryptContext
from src.models import User
from datetime import datetime, timedelta
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify(password, hash_password):
    return pwd_context.verify(password, hash_password)

def check_user_password_is_correct(db, name, password):
    user = db.query(User).filter(User.username == name).first()
    if not verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data, expires_delta=None):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, '1892dhianiandowqd0n', algorithm="HS256")
    return encoded_jwt