from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db.database import get_db
from app.services import machine_service
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.machine import MachineResponse

router = APIRouter(
    prefix="/machines",
    tags=["Пральні машини"]
)

@router.get("/")
def read_active_machines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отримати список усіх активних пральних машин.
    Використовується на фронтенді для заповнення випадаючого списку.
    """
    machines = machine_service.get_active_machines(db)
    return [MachineResponse.model_validate(machine) for machine in machines]


@router.get("/{machine_id}/schedule")
def read_machine_schedule(
    machine_id: int,
    target_date: date = Query(..., description="Дата для розкладу у форматі YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отримати розклад (вільні/зайняті слоти) для конкретної машинки на обрану дату.
    """
    schedule = machine_service.get_machine_schedule(
        db=db, 
        machine_id=machine_id, 
        target_date=target_date
    )
    return schedule