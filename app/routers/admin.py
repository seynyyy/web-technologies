from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from datetime import date
import logging
from app.db.database import get_db
from app.core.security import get_current_admin
from app.core import scheduler as scheduler_module
from app.models.user import User
from app.models.machine import WashingMachine
from app.models.booking import Booking
from app.schemas.machine import MachineCreate, MachineUpdate, MachineResponse
from app.schemas.user import UserAdminUpdate

audit_logger = logging.getLogger("app.audit.admin")


def log_admin_action(admin: User, action: str, target: str, target_id: int | None = None, details: dict | None = None):
    """Write structured admin audit logs for traceability."""
    audit_logger.info(
        "ADMIN_ACTION action=%s admin_id=%s admin_name=%s target=%s target_id=%s details=%s",
        action,
        admin.id,
        admin.full_name,
        target,
        target_id,
        details or {},
    )

router = APIRouter(
    prefix="/admin-api",
    tags=["Admin Operations"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)):
    """Ключові метрики для адмін панелі"""
    users_count = db.query(User).count()
    machines_count = db.query(WashingMachine).count()
    active_machines = db.query(WashingMachine).filter(WashingMachine.is_active == True).count()
    today_bookings = db.query(Booking).filter(Booking.date == date.today()).count()
    return {
        "users": users_count,
        "machines": machines_count,
        "active_machines": active_machines,
        "today_bookings": today_bookings
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Отримати список усіх користувачів для таблиці"""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "telegram_id": user.telegram_id,
            "washes_left": user.washes_left,
            "washes_used_this_month": user.washes_used_this_month,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "has_discount": user.has_discount,
            "notify": user.notify
        }
        for user in users
    ]

@router.post("/users/{user_id}/adjust-washes")
def adjust_washes(user_id: int, delta: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """Додати або відняти прання вручну"""
    user = db.get(User, user_id)
    if user is None:
        log_admin_action(current_admin, "adjust_washes_failed", "user", user_id, {"delta": delta, "reason": "user_not_found"})
        return {"status": "error", "message": "User not found"}

    previous_balance = user.washes_left
    user.washes_left += delta
    db.commit()

    log_admin_action(
        current_admin,
        "adjust_washes",
        "user",
        user_id,
        {
            "delta": delta,
            "previous_washes_left": previous_balance,
            "new_washes_left": user.washes_left,
        },
    )
    return {"status": "success", "new_balance": user.washes_left}


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Оновити дані користувача"""
    user = db.get(User, user_id)
    if user is None:
        log_admin_action(current_admin, "update_user_failed", "user", user_id, {"reason": "user_not_found"})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    
    if "full_name" in update_data and update_data["full_name"]:
        existing = db.query(User).filter(User.full_name == update_data["full_name"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ПІБ вже використовується")
        user.full_name = update_data["full_name"]
    
    if "washes_left" in update_data:
        user.washes_left = update_data["washes_left"]
    
    if "washes_used_this_month" in update_data:
        user.washes_used_this_month = update_data["washes_used_this_month"]
    
    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]
    
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    
    if "has_discount" in update_data:
        user.has_discount = update_data["has_discount"]
    
    db.commit()
    db.refresh(user)

    log_admin_action(current_admin, "update_user", "user", user_id, {"updated_fields": list(update_data.keys())})

    return {
        "id": user.id,
        "full_name": user.full_name,
        "telegram_id": user.telegram_id,
        "washes_left": user.washes_left,
        "washes_used_this_month": user.washes_used_this_month,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "has_discount": user.has_discount,
        "notify": user.notify
    }


@router.get("/machines", response_model=list[MachineResponse])
def list_machines(db: Session = Depends(get_db)):
    machines = db.query(WashingMachine).order_by(WashingMachine.id.asc()).all()
    return [MachineResponse.model_validate(machine) for machine in machines]


@router.post("/machines", status_code=status.HTTP_201_CREATED, response_model=MachineResponse)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    machine = WashingMachine(name=payload.name, is_active=payload.is_active)
    db.add(machine)
    db.commit()
    db.refresh(machine)

    log_admin_action(
        current_admin,
        "create_machine",
        "machine",
        machine.id,
        {"name": machine.name, "is_active": machine.is_active},
    )

    return MachineResponse.model_validate(machine)


@router.patch("/machines/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    payload: MachineUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    machine = db.get(WashingMachine, machine_id)
    if machine is None:
        log_admin_action(current_admin, "update_machine_failed", "machine", machine_id, {"reason": "machine_not_found"})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    old_values = {"name": machine.name, "is_active": machine.is_active}

    if payload.name is not None:
        machine.name = payload.name
    if payload.is_active is not None:
        machine.is_active = payload.is_active

    db.commit()
    db.refresh(machine)

    log_admin_action(
        current_admin,
        "update_machine",
        "machine",
        machine_id,
        {
            "old": old_values,
            "new": {"name": machine.name, "is_active": machine.is_active},
        },
    )

    return MachineResponse.model_validate(machine)


@router.delete("/machines/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(machine_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    machine = db.get(WashingMachine, machine_id)
    if machine is None:
        log_admin_action(current_admin, "delete_machine_failed", "machine", machine_id, {"reason": "machine_not_found"})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    deleted_snapshot = {"name": machine.name, "is_active": machine.is_active}
    db.delete(machine)
    db.commit()

    log_admin_action(current_admin, "delete_machine", "machine", machine_id, deleted_snapshot)

    return None


@router.get("/bookings")
def list_bookings(
    limit: int = 50, 
    date_filter: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db)
):
    """
    Отримати список бронювань з фільтрацією
    - date_filter: конкретна дата (deprecated, використовуйте date_from/date_to)
    - date_from: початкова дата діапазону
    - date_to: кінцева дата діапазону
    """
    query = db.query(Booking).options(
        joinedload(Booking.user)
    )
    
    if date_filter:
        query = query.filter(Booking.date == date_filter)
    else:
        if date_from:
            query = query.filter(Booking.date >= date_from)
        if date_to:
            query = query.filter(Booking.date <= date_to)
    
    bookings = query.order_by(Booking.created_at.desc()).limit(limit).all()
    return [
        {
            "id": booking.id,
            "user_id": booking.user_id,
            "user_full_name": booking.user.full_name if booking.user else "Unknown",
            "user_telegram_id": booking.user.telegram_id if booking.user else None,
            "machine_id": booking.machine_id,
            "date": booking.date,
            "time_slot": booking.time_slot.value,
            "created_at": booking.created_at
        }
        for booking in bookings
    ]


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """Видалити бронювання"""
    booking = db.get(Booking, booking_id)
    if booking is None:
        log_admin_action(current_admin, "delete_booking_failed", "booking", booking_id, {"reason": "booking_not_found"})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    deleted_snapshot = {
        "user_id": booking.user_id,
        "machine_id": booking.machine_id,
        "date": str(booking.date),
        "time_slot": booking.time_slot.value,
    }
    db.delete(booking)
    db.commit()

    log_admin_action(current_admin, "delete_booking", "booking", booking_id, deleted_snapshot)

    return None


@router.get("/scheduler/jobs")
def get_scheduler_jobs(current_admin: User = Depends(get_current_admin)):
    """Debug endpoint: показує всі заплановані завдання в scheduler"""
    if not scheduler_module.scheduler:
        log_admin_action(current_admin, "view_scheduler_jobs", "scheduler", details={"status": "not_initialized"})
        return {
            "status": "error",
            "message": "Scheduler not initialized",
            "jobs": []
        }
    
    jobs = scheduler_module.scheduler.get_jobs()
    
    result = {
        "status": "ok",
        "scheduler_running": scheduler_module.scheduler.running,
        "total_jobs": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "func": str(job.func),
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "args": str(job.args),
                "kwargs": str(job.kwargs)
            }
            for job in jobs
        ]
    }

    log_admin_action(current_admin, "view_scheduler_jobs", "scheduler", details={"total_jobs": len(jobs)})

    return result