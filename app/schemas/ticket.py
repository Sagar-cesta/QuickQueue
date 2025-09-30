from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.ticket import Priority, Status


class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: Priority = Priority.MEDIUM
    status: Status = Status.OPEN


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[Priority] = None
    status: Optional[Status] = None


class TicketInDB(TicketBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Ticket(TicketInDB):
    pass
