from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.models import Ticket, Comment
from app.schemas.ticket import CommentIn, CommentOut

router = APIRouter()


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    ticket_id: int, 
    comment: CommentIn, 
    db: Session = Depends(get_db)
):
    """Add comment to ticket"""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db_comment = Comment(
        ticket_id=ticket_id,
        author=comment.author,
        body=comment.body
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.get("/{ticket_id}/comments", response_model=List[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    """List comments for a ticket (newest first)"""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comments = db.query(Comment).filter(Comment.ticket_id == ticket_id).order_by(Comment.created_at.desc()).all()
    return comments
