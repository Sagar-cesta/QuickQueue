from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate


def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Get a ticket by ID"""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets(db: Session, skip: int = 0, limit: int = 100) -> List[Ticket]:
    """Get all tickets with pagination"""
    return db.query(Ticket).offset(skip).limit(limit).all()


def create_ticket(db: Session, ticket: TicketCreate) -> Ticket:
    """Create a new ticket"""
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        status=ticket.status
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket: TicketUpdate) -> Ticket:
    """Update a ticket"""
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if db_ticket:
        update_data = ticket.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_ticket, field, value)
        db.commit()
        db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    """Delete a ticket"""
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if db_ticket:
        db.delete(db_ticket)
        db.commit()
        return True
    return False
