from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta
import logging
from app.models.booking import Booking
from app.models.machine import WashingMachine
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.core import scheduler as scheduler_module
from app.services.notification_service import send_end_notification, send_start_notification
from apscheduler.jobstores.base import JobLookupError

logger = logging.getLogger(__name__)

MAX_WASHES_PER_MONTH = 12
NOTIFICATION_MISFIRE_GRACE_SECONDS = 60

def calculate_start_time(booking_date: date, time_slot) -> datetime:
    """Calculate the start datetime from booking date and time slot."""
    slot_hour_str = time_slot.value.split('-')[0]
    slot_hour = int(slot_hour_str.split(':')[0])
    slot_minute = int(slot_hour_str.split(':')[1]) if ':' in slot_hour_str else 0
    return datetime.combine(booking_date, datetime.min.time()).replace(hour=slot_hour, minute=slot_minute)

def calculate_end_time(booking_date: date, time_slot) -> datetime:
    """Calculate the end datetime from booking date and time slot (assumes 1 hour duration)."""
    start_time = calculate_start_time(booking_date, time_slot)
    return start_time + timedelta(hours=1)

def create_booking(db: Session, booking_in: BookingCreate, user: User):
    """
    Створює нове бронювання з усіма перевірками бізнес-логіки.
    """
    
    washes_left = user.washes_left if user.washes_left is not None else 0
    if washes_left <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="У вас немає доступних прань")
    
    if user.washes_used_this_month >= MAX_WASHES_PER_MONTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Ви використали ліміт прань на місяць ({MAX_WASHES_PER_MONTH})"
        )
        
    today = date.today()
    if booking_in.date < today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неможливо забронювати на минулу дату")
        
    if booking_in.date == today:
        now = datetime.now()
        slot_hour_str = booking_in.time_slot.value.split('-')[0]
        slot_hour = int(slot_hour_str.split(':')[0])
        
        if slot_hour <= now.hour:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неможливо забронювати на минулу годину")

    machine = db.query(WashingMachine).filter(WashingMachine.id == booking_in.machine_id, WashingMachine.is_active == True).first()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пральну машину не знайдено або вона неактивна")

    existing_booking = db.query(Booking).filter(
        Booking.machine_id == booking_in.machine_id,
        Booking.date == booking_in.date,
        Booking.time_slot == booking_in.time_slot
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Цей слот вже зайнятий")

    new_booking = Booking(
        user_id=user.id,
        machine_id=booking_in.machine_id,
        date=booking_in.date,
        time_slot=booking_in.time_slot
    )
    
    user.washes_left -= 1
    user.washes_used_this_month += 1
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    start_datetime = calculate_start_time(new_booking.date, new_booking.time_slot)
    end_datetime = calculate_end_time(new_booking.date, new_booking.time_slot)

    # Зберігаємо ID завдань (job_id), щоб мати змогу їх скасувати, 
    # якщо користувач вирішить скасувати бронювання
    start_job_id = f"start_{new_booking.id}"
    end_job_id = f"end_{new_booking.id}"

    logger.info(f"📅 Scheduling notifications for booking {new_booking.id}")
    logger.info(f"   Start notification: {start_datetime} (telegram_id={user.telegram_id}, machine={machine.name}, notify={user.notify})")
    logger.info(f"   End notification: {end_datetime} (telegram_id={user.telegram_id}, machine={machine.name}, notify={user.notify})")

    # Додаємо завдання у плануваль ник тільки якщо користувач підключив Telegram і увімкнув сповіщення
    if scheduler_module.scheduler and user.telegram_id and user.notify:
        try:
            scheduler_module.scheduler.add_job(
                send_start_notification, 
                trigger='date',          
                run_date=start_datetime, 
                args=[user.telegram_id, machine.name], 
                id=start_job_id,               
                replace_existing=True,
                misfire_grace_time=NOTIFICATION_MISFIRE_GRACE_SECONDS
            )
            logger.info(f"✅ Start job added: {start_job_id}")
        except Exception as e:
            logger.error(f"❌ Failed to add start job: {e}")
        
        try:
            scheduler_module.scheduler.add_job(
                send_end_notification, 
                trigger='date', 
                run_date=end_datetime, 
                args=[user.telegram_id, machine.name], 
                id=end_job_id, 
                replace_existing=True,
                misfire_grace_time=NOTIFICATION_MISFIRE_GRACE_SECONDS
            )
            logger.info(f"✅ End job added: {end_job_id}")
        except Exception as e:
            logger.error(f"❌ Failed to add end job: {e}")
        
        # Show all scheduled jobs for debug
        jobs = scheduler_module.scheduler.get_jobs()
        logger.info(f"📋 Total scheduled jobs: {len(jobs)}")
        for job in jobs:
            logger.debug(f"   - Job {job.id}: next run at {job.next_run_time}")
    elif not user.telegram_id:
        logger.info("ℹ️ Telegram not connected - notifications skipped")
    elif not user.notify:
        logger.info("ℹ️ Notifications disabled by user - notifications skipped")
    else:
        logger.warning("⚠️ Scheduler is not initialized!")
    
    return new_booking


def cancel_booking(db: Session, booking_id: int, user: User):
    """
    Скасовує бронювання і повертає прання на баланс.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == user.id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронювання не знайдено")
        
    slot_hour_str = booking.time_slot.value.split('-')[0]
    slot_hour = int(slot_hour_str.split(':')[0])
    slot_minute = int(slot_hour_str.split(':')[1]) if ':' in slot_hour_str else 0
        
    booking_datetime = datetime.combine(booking.date, datetime.min.time()).replace(hour=slot_hour, minute=slot_minute)
    now = datetime.now()
    
    if booking_datetime - now < timedelta(hours=2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Неможливо скасувати бронювання менш ніж за 2 години до початку"
        )
        
    user.washes_left += 1
    user.washes_used_this_month -= 1
    
    db.delete(booking)
    db.commit()
    
    start_job_id = f"start_{booking.id}"
    end_job_id = f"end_{booking.id}"
    
    logger.info(f"🗑️ Removing scheduled notifications for booking {booking.id}")
    
    if scheduler_module.scheduler:
        try:
            scheduler_module.scheduler.remove_job(start_job_id)
            logger.info(f"✅ Removed start job: {start_job_id}")
        except JobLookupError:
            logger.warning(f"⚠️ Start job not found: {start_job_id}")
        try:
            scheduler_module.scheduler.remove_job(end_job_id)
            logger.info(f"✅ Removed end job: {end_job_id}")
        except JobLookupError:
            logger.warning(f"⚠️ End job not found: {end_job_id}")
    else:
        logger.warning("⚠️ Scheduler is not initialized!")
    
    return {"success": True, "washes_left": user.washes_left, "washes_used_this_month": user.washes_used_this_month}