from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from enum import Enum

class TimeSlotEnum(str, Enum):
    SLOT_1 = "7:00-9:30"
    SLOT_2 = "10:00-12:30"
    SLOT_3 = "13:00-15:30"
    SLOT_4 = "16:00-18:30"
    SLOT_5 = "19:00-21:30"

class BookingBase(BaseModel):
    machine_id: int
    date: date
    time_slot: TimeSlotEnum

class BookingCreate(BookingBase):
    pass 


class BookingResponse(BookingBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)