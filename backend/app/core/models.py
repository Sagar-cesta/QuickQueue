from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(160), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False, index=True)
    status = Column(Enum(Status), default=Status.OPEN, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assigned_to = Column(Integer, nullable=True)  # Future use for user assignment
    
    # Relationships
    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_tickets_status_priority', 'status', 'priority'),
    )
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status}')>"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    author = Column(String(100), nullable=False)  # Simple stub for now
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, ticket_id={self.ticket_id}, author='{self.author}')>"
