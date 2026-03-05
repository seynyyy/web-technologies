from fastapi import Form
from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    telegram_id: Optional[int] = None
    notify: Optional[bool] = False
    
class UserCreate(BaseModel):
    full_name: str
    password: str
    telegram_id: Optional[int] = None
    notify: Optional[bool] = False


class AuthLoginRequest(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...)
    ) -> "AuthLoginRequest":
        return cls(username=username, password=password)


class AuthRegisterRequest(BaseModel):
    full_name: str
    password: str
    password_confirm: str
    notify: Optional[bool] = False

    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        password: str = Form(...),
        password_confirm: str = Form(...)
    ) -> "AuthRegisterRequest":
        return cls(
            full_name=full_name,
            password=password,
            password_confirm=password_confirm,
            notify=False
        )


class AuthChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @classmethod
    def as_form(
        cls,
        current_password: str = Form(...),
        new_password: str = Form(...)
    ) -> "AuthChangePasswordRequest":
        return cls(current_password=current_password, new_password=new_password)


class AuthUpdateProfileRequest(BaseModel):
    full_name: str

    @classmethod
    def as_form(cls, full_name: str = Form(...)) -> "AuthUpdateProfileRequest":
        return cls(full_name=full_name)
    
class UserRead(UserBase):
    pass

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    telegram_id: int | None = None
    notify: bool | None = None

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