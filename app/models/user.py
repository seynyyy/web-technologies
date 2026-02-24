from typing import Optional, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    telegram_id: Mapped[Optional[int]] = mapped_column(unique=True, index=True, nullable=True)
    washes_left: Mapped[int] = mapped_column(default=0)
    washes_used_this_month: Mapped[int] = mapped_column(default=0)
    has_discount: Mapped[bool] = mapped_column(default=False)
    notify: Mapped[bool] = mapped_column(default=True)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, full_name='{self.full_name}', telegram_id={self.telegram_id})>"

    def __str__(self) -> str:
        return f"User(id={self.id}, full_name='{self.full_name}', telegram_id={self.telegram_id})"