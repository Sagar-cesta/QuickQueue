from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import json
import os

# Simple in-memory storage for demo purposes
tickets_db = []
comments_db = []

# Pydantic models
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketIn(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.MEDIUM

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
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

class CommentIn(BaseModel):
    author: str
    body: str

class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author: str
    body: str
    created_at: datetime

# Initialize FastAPI app
app = FastAPI(
    title="QuickQueue",
    description="Ticketing/Helpdesk Queue System",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.post("/api/v1/tickets/", response_model=TicketOut, status_code=201)
def create_ticket(ticket: TicketIn):
    """Create a new ticket"""
    ticket_id = len(tickets_db) + 1
    new_ticket = TicketOut(
        id=ticket_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority,
        status=Status.OPEN,
        created_at=datetime.now(),
        updated_at=None
    )
    tickets_db.append(new_ticket)
    return new_ticket

@app.get("/api/v1/tickets/", response_model=List[TicketOut])
def list_tickets(
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """List tickets with filters and pagination"""
    filtered_tickets = tickets_db.copy()
    
    if status:
        filtered_tickets = [t for t in filtered_tickets if t.status == status]
    if priority:
        filtered_tickets = [t for t in filtered_tickets if t.priority == priority]
    if q:
        filtered_tickets = [t for t in filtered_tickets if q.lower() in t.title.lower()]
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    return filtered_tickets[start:end]

@app.get("/api/v1/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int):
    """Get ticket details"""
    for ticket in tickets_db:
        if ticket.id == ticket_id:
            return ticket
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Ticket not found")

@app.patch("/api/v1/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, ticket_update: TicketUpdate):
    """Update ticket"""
    for i, ticket in enumerate(tickets_db):
        if ticket.id == ticket_id:
            update_data = ticket_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(ticket, field, value)
            ticket.updated_at = datetime.now()
            tickets_db[i] = ticket
            return ticket
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Ticket not found")

@app.delete("/api/v1/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int):
    """Delete ticket"""
    global tickets_db
    tickets_db = [t for t in tickets_db if t.id != ticket_id]
    return None

@app.post("/api/v1/tickets/{ticket_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(ticket_id: int, comment: CommentIn):
    """Add comment to ticket"""
    # Verify ticket exists
    ticket_exists = any(t.id == ticket_id for t in tickets_db)
    if not ticket_exists:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment_id = len(comments_db) + 1
    new_comment = CommentOut(
        id=comment_id,
        ticket_id=ticket_id,
        author=comment.author,
        body=comment.body,
        created_at=datetime.now()
    )
    comments_db.append(new_comment)
    return new_comment

@app.get("/api/v1/tickets/{ticket_id}/comments", response_model=List[CommentOut])
def list_comments(ticket_id: int):
    """List comments for a ticket"""
    # Verify ticket exists
    ticket_exists = any(t.id == ticket_id for t in tickets_db)
    if not ticket_exists:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket_comments = [c for c in comments_db if c.ticket_id == ticket_id]
    return sorted(ticket_comments, key=lambda x: x.created_at, reverse=True)

@app.get("/api/v1/summary/")
def get_summary():
    """Get ticket counts grouped by status and priority"""
    by_status = {status.value: 0 for status in Status}
    by_priority = {priority.value: 0 for priority in Priority}
    
    for ticket in tickets_db:
        by_status[ticket.status.value] += 1
        by_priority[ticket.priority.value] += 1
    
    return {
        "by_status": by_status,
        "by_priority": by_priority
    }

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - show last 20 tickets"""
    recent_tickets = sorted(tickets_db, key=lambda x: x.created_at, reverse=True)[:20]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tickets": recent_tickets
    })

@app.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Show create ticket form"""
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
async def create_ticket_form(request: Request):
    """Handle create ticket form submission"""
    # Get form data from request
    form_data = await request.form()
    title = form_data.get("title")
    description = form_data.get("description")
    priority = form_data.get("priority")
    
    if not title or not description or not priority:
        return templates.TemplateResponse("create.html", {
            "request": request,
            "error": "All fields are required!"
        })
    
    try:
        priority_enum = Priority(priority.lower())
    except ValueError:
        return templates.TemplateResponse("create.html", {
            "request": request,
            "error": "Invalid priority value!"
        })
    
    ticket = TicketIn(title=title, description=description, priority=priority_enum)
    created_ticket = create_ticket(ticket)
    
    return templates.TemplateResponse("create.html", {
        "request": request,
        "success": f"Ticket #{created_ticket.id} created successfully!"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
