from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    telegram_id: Optional[int] = None
    
class UserCreate(BaseModel):
    full_name: str
    password: str
    telegram_id: Optional[int] = None
    
class UserRead(UserBase):
    pass

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    telegram_id: int | None = None

class UserAdminUpdate(BaseModel):
    """Схема для оновлення користувача адміністратором"""
    full_name: str | None = None
    washes_left: int | None = None
    washes_used_this_month: int | None = None
    is_admin: bool | None = None
    is_active: bool | None = None
    has_discount: bool | None = None
    
class UserResponse(UserBase):
    id: int
    full_name: str
    telegram_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
    

class TelegramLoginData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str