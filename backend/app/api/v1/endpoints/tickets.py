from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_pagination
from app.core.models import Ticket, Priority, Status
from app.schemas.ticket import TicketIn, TicketOut, TicketUpdate

router = APIRouter()


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketIn, db: Session = Depends(get_db)):
    """Create a new ticket"""
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.get("/", response_model=List[TicketOut])
def list_tickets(
    status: Optional[Status] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    q: Optional[str] = Query(None, description="Search in title"),
    pagination: dict = Depends(get_pagination),
    db: Session = Depends(get_db)
):
    """List tickets with filters and pagination"""
    query = db.query(Ticket)
    
    # Apply filters
    filters = []
    if status:
        filters.append(Ticket.status == status)
    if priority:
        filters.append(Ticket.priority == priority)
    if q:
        filters.append(Ticket.title.contains(q))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply pagination
    skip = (pagination["page"] - 1) * pagination["page_size"]
    tickets = query.offset(skip).limit(pagination["page_size"]).all()
    
    return tickets


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get ticket details"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int, 
    ticket_update: TicketUpdate, 
    db: Session = Depends(get_db)
):
    """Update ticket"""
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update fields
    update_data = ticket_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete ticket"""
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db.delete(db_ticket)
    db.commit()
    return None
