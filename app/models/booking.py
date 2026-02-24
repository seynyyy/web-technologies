from datetime import date, datetime
import enum
from sqlalchemy import ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.machine import WashingMachine
from app.models.user import User

class TimeSlotEnum(str, enum.Enum):
    SLOT_1 = "7:00-9:30"
    SLOT_2 = "10:00-12:30"
    SLOT_3 = "13:00-15:30"
    SLOT_4 = "16:00-18:30"
    SLOT_5 = "19:00-21:30"

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("washing_machines.id", ondelete="CASCADE"))
    
    booking_date: Mapped[date] = mapped_column(index=True)

    date = synonym("booking_date")
    
    time_slot: Mapped[TimeSlotEnum] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="bookings")
    machine: Mapped["WashingMachine"] = relationship(back_populates="bookings")

    __table_args__ = (
        UniqueConstraint('machine_id', 'booking_date', 'time_slot', name='uix_machine_date_slot'),
        Index('idx_machine_date', 'machine_id', 'booking_date'),
    )