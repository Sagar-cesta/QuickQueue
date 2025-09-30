from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.models import Ticket, Priority, Status

router = APIRouter()


@router.get("/")
def get_summary(db: Session = Depends(get_db)):
    """Get ticket counts grouped by status and priority"""
    # Count by status
    status_counts = db.query(
        Ticket.status, 
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.status).all()
    
    # Count by priority
    priority_counts = db.query(
        Ticket.priority, 
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.priority).all()
    
    # Format results
    by_status = {status.value: 0 for status in Status}
    by_priority = {priority.value: 0 for priority in Priority}
    
    for status, count in status_counts:
        by_status[status.value] = count
    
    for priority, count in priority_counts:
        by_priority[priority.value] = count
    
    return {
        "by_status": by_status,
        "by_priority": by_priority
    }
