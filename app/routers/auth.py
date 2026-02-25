from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token, verify_telegram_data, get_current_user, get_password_hash
from app.schemas.user import TelegramLoginData, UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Авторизація"])

class NotificationSettings(BaseModel):
    notify: bool

@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.full_name == form_data.username).first()
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.full_name})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register_user(
    full_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Паролі не збігаються"
        )
    
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль має містити мінімум 6 символів"
        )
    
    user_in = UserCreate(full_name=full_name, password=password, telegram_id=None, notify=False)
    
    try:
        user = user_service.create_user(db, user_in)
        access_token = create_access_token(data={"sub": user.full_name})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) or "Не вдалося зареєструвати користувача"
        ) from e
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "telegram_id": user.telegram_id
        }
    }


@router.post("/login/telegram")
def login_with_telegram(
    payload: TelegramLoginData,
    db: Session = Depends(get_db)
):
    data = payload.model_dump()
    if not verify_telegram_data(data.copy()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані Telegram"
        )

    user = db.query(User).filter(User.telegram_id == payload.id).first()
    if not user:
        name_parts = [payload.first_name, payload.last_name]
        full_name = " ".join(part for part in name_parts if part)
        if not full_name and payload.username:
            full_name = payload.username
        if not full_name:
            full_name = f"tg_{payload.id}"

        base_name = full_name
        counter = 1
        while db.query(User).filter(User.full_name == full_name).first():
            full_name = f"{base_name}_{counter}"
            counter += 1

        user = User(
            full_name=full_name,
            telegram_id=payload.id,
            hashed_password=None,
            is_active=True,
            is_admin=False,
            washes_left=0,
            washes_used_this_month=0,
            has_discount=False,
            notify=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.full_name})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/change-password")
def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.hashed_password or not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний поточний пароль"
        )
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"status": "success", "message": "Пароль успішно змінено"}


@router.post("/update-profile")
def update_profile(
    full_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(User).filter(User.full_name == full_name, User.id != current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Це ім'я вже використовується іншим користувачем"
        )
    
    current_user.full_name = full_name
    db.commit()
    
    access_token = create_access_token(data={"sub": current_user.full_name})
    return {"status": "success", "message": "Профіль оновлено", "access_token": access_token}


@router.post("/link-telegram")
def link_telegram(
    payload: TelegramLoginData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Приєднати Telegram акаунт до профілю через автентифікацію"""
    # Verify telegram data
    data = payload.model_dump()
    if not verify_telegram_data(data.copy()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані Telegram"
        )
    
    # Check if telegram_id is already linked to another user
    existing = db.query(User).filter(User.telegram_id == payload.id, User.id != current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Цей Telegram акаунт вже пов'язаний з іншим користувачем"
        )
    
    current_user.telegram_id = payload.id
    db.commit()
    
    return {"status": "success", "message": "Telegram акаунт успішно приєднано"}


@router.post("/update-notification-settings")
def update_notification_settings(
    settings: NotificationSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Оновити налаштування сповіщень користувача"""
    if not current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram акаунт не підключено. Підключіть Telegram для отримання сповіщень."
        )
    
    current_user.notify = settings.notify
    db.commit()
    
    message = "Сповіщення увімкнено" if settings.notify else "Сповіщення вимкнено"
    return {"status": "success", "message": message}