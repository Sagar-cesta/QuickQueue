from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.models import Priority, Status


class TicketIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=160, description="Ticket title")
    description: str = Field(..., min_length=1, description="Ticket description")
    priority: Priority = Field(Priority.MEDIUM, description="Ticket priority")


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[Priority] = None
    status: Optional[Status] = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_to: Optional[int] = None

    class Config:
        from_attributes = True


class CommentIn(BaseModel):
    author: str = Field(..., min_length=1, max_length=100, description="Comment author")
    body: str = Field(..., min_length=1, description="Comment body")


class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True
