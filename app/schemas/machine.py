from pydantic import BaseModel, ConfigDict
from typing import Optional

class MachineBase(BaseModel):
    name: str
    is_active: bool = True

class MachineCreate(MachineBase):
    pass

class MachineResponse(MachineBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None