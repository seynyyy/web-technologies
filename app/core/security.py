from dotenv import load_dotenv
import os
load_dotenv()

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from time import time
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError 
from app.db.database import get_db
from app.models.user import User

_SECRET_KEY = os.getenv("SECRET_KEY")
_TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not _SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

if not _TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

SECRET_KEY: str = _SECRET_KEY
TELEGRAM_BOT_TOKEN: str = _TELEGRAM_BOT_TOKEN

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевірити пароль проти хешу"""
    return bcrypt.checkpw(plain_password[:72].encode(), hashed_password.encode())

def get_password_hash(password: str) -> str:
    """Хешувати пароль з bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password[:72].encode(), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.full_name == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="У вас немає прав доступу до цієї сторінки"
        )
    return current_user

def verify_telegram_data(data: dict) -> bool:
    """Перевіряє криптографічний підпис Telegram"""
    
    received_hash = data.pop('hash')
    
    if time() - data.get('auth_date', 0) > 86400:
        return False

    data_check_arr = []
    for key, value in sorted(data.items()):
        if value is not None:
            data_check_arr.append(f"{key}={value}")
    data_check_string = "\n".join(data_check_arr)

    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    
    calculated_hash = hmac.new(
        secret_key, 
        data_check_string.encode(), 
        hashlib.sha256
    ).hexdigest()

    return calculated_hash == received_hash