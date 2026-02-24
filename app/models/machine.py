from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking

class WashingMachine(Base):
    __tablename__ = "washing_machines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(64))
    
    is_active: Mapped[bool] = mapped_column(default=True)


    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="machine")