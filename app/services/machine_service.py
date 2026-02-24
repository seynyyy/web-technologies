from sqlalchemy.orm import Session
from datetime import date
from fastapi import HTTPException, status

from app.models.machine import WashingMachine
from app.models.booking import Booking, TimeSlotEnum

def get_active_machines(db: Session):
    """
    Повертає список усіх активних пральних машин.
    """
    return db.query(WashingMachine).filter(WashingMachine.is_active == True).all()

def get_machine_schedule(db: Session, machine_id: int, target_date: date):
    """
    Повертає статус усіх слотів (вільно/зайнято) 
    для конкретної машинки на обрану дату.
    """
    machine = db.query(WashingMachine).filter(WashingMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Машинку не знайдено"
        )

    bookings = db.query(Booking).filter(
        Booking.machine_id == machine_id,
        Booking.date == target_date
    ).all()

    booked_slots = {booking.time_slot for booking in bookings}

    schedule = []
    for slot in TimeSlotEnum:
        schedule.append({
            "time_slot": slot.value,
            "status": "booked" if slot in booked_slots else "free"
        })
        
    return schedule