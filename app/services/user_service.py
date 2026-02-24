from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def get_user_by_username(db: Session, full_name: str):
    """Шукає користувача за його логіном"""
    return db.query(User).filter(User.full_name == full_name).first()

def get_user_by_telegram(db: Session, telegram_id: int):
    """Шукає користувача за Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, user_in: UserCreate):
    """
    Створює нового користувача. 
    Перевіряє унікальність логіна та безпечно хешує пароль.
    """
    existing_user = get_user_by_username(db, full_name=user_in.full_name)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такий користувач вже існує"
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    telegram = user_in.telegram_id
        
    db_user = User(
        full_name=user_in.full_name,
        telegram_id=telegram,
        hashed_password=hashed_password,
        
        washes_left=0,
        washes_used_this_month=0,
        has_discount=False,
        notify=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def reset_monthly_washes(db: Session, user: User):
    """
    Обнуляє лічильник прань за місяць. 
    Раніше це був метод `reset_monthly_washes` у вашій моделі Django.
    """
    db.query(User).filter(User.id == user.id).update({User.washes_used_this_month: 0})
    db.commit()
    db.refresh(user)
    return user