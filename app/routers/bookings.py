from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingResponse
from app.services import booking_service

router = APIRouter(
    prefix="/bookings",
    tags=["Бронювання"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookingResponse)
def create_new_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Створити нове бронювання.
    Перевіряє ліміти прань, доступність слота та планує відправку повідомлень у Telegram.
    """
    # Вся складна логіка (включно зі збереженням завдань у планувальник)
    # тепер надійно захована у нашому сервісі!
    booking = booking_service.create_booking(
        db=db, 
        booking_in=booking_in, 
        user=current_user
    )
    return booking


@router.get("/my", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отримати список усіх бронювань поточного користувача.
    Корисно для відображення історії в особистому кабінеті.
    """
    # Оскільки запит дуже простий, можемо зробити його прямо тут,
    # або винести в booking_service.get_user_bookings(db, current_user.id)
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).order_by(Booking.date.desc()).all()
    
    return bookings


@router.delete("/{booking_id}")
def cancel_existing_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Скасувати бронювання.
    Повертає прання на баланс та видаляє заплановані повідомлення з планувальника.
    """
    result = booking_service.cancel_booking(
        db=db, 
        booking_id=booking_id, 
        user=current_user
    )
    return result