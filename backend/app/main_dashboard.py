from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum
import json
import os

# Enhanced in-memory storage for demo purposes
tickets_db = []
comments_db = []
users_db = []
analytics_db = {
    "monthly_metrics": {},
    "yearly_metrics": {},
    "repeat_tickets": []
}

# Initialize with sample data
def init_sample_data():
    """Initialize with sample data for demo"""
    global users_db, tickets_db
    
    # Sample users
    users_db.extend([
        {
            "id": 1, "username": "admin", "email": "admin@quickqueue.com", 
            "full_name": "Admin User", "role": "admin", "is_active": True,
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Qz8Qz2",  # password: admin123
            "created_at": datetime.now()
        },
        {
            "id": 2, "username": "agent1", "email": "agent@quickqueue.com", 
            "full_name": "Support Agent", "role": "agent", "is_active": True,
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Qz8Qz2",  # password: agent123
            "created_at": datetime.now()
        },
        {
            "id": 3, "username": "user1", "email": "user@quickqueue.com", 
            "full_name": "Regular User", "role": "user", "is_active": True,
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Qz8Qz2",  # password: user123
            "created_at": datetime.now()
        }
    ])
    
    # Sample tickets
    tickets_db.extend([
        {
            "id": 1, "title": "Login Issue", "description": "Cannot login to the system",
            "priority": "high", "status": "open", "created_by": 3, "assigned_to": 2,
            "created_at": datetime.now() - timedelta(days=2),
            "updated_at": None, "tags": ["login", "authentication"]
        },
        {
            "id": 2, "title": "Password Reset", "description": "Need to reset password",
            "priority": "medium", "status": "in_progress", "created_by": 3, "assigned_to": 2,
            "created_at": datetime.now() - timedelta(days=1),
            "updated_at": datetime.now() - timedelta(hours=2), "tags": ["password"]
        },
        {
            "id": 3, "title": "Feature Request", "description": "Add dark mode support",
            "priority": "low", "status": "resolved", "created_by": 3, "assigned_to": 2,
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now() - timedelta(days=1), "tags": ["feature", "ui"]
        }
    ])

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

class UserRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"

class TicketIn(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    tags: List[str] = []

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    assigned_to: Optional[int] = None
    tags: Optional[List[str]] = None

class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_by: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    tags: List[str]
    created_by_name: Optional[str] = None
    assigned_to_name: Optional[str] = None

class CommentIn(BaseModel):
    body: str

class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    author_name: str
    body: str
    created_at: datetime

class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    monthly_tickets: int
    yearly_tickets: int
    repeat_tickets: int

# Initialize FastAPI app
app = FastAPI(
    title="QuickQueue Dashboard",
    description="Advanced Ticketing/Helpdesk Queue System",
    version="2.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize sample data
init_sample_data()

# Authentication endpoints
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login"""
    # Simple password check for demo (in production, use proper hashing)
    user = next((u for u in users_db if u["username"] == username and u["is_active"]), None)
    
    if not user or password != "admin123":  # Demo password
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })
    
    # Create session (simplified for demo)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="user_id", value=str(user["id"]))
    response.set_cookie(key="user_role", value=user["role"])
    response.set_cookie(key="username", value=user["username"])
    return response

@app.get("/logout")
async def logout():
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="user_id")
    response.delete_cookie(key="user_role")
    response.delete_cookie(key="username")
    return response

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    recent_tickets = get_recent_tickets()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_tickets": recent_tickets
    })

# Ticket management endpoints
@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request, status: str = "all"):
    """Tickets management page"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    tickets = get_tickets_by_status(status)
    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "tickets": tickets,
        "current_status": status
    })

@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_id: int):
    """Ticket detail page"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    ticket = get_ticket_by_id(ticket_id)
    comments = get_comments_by_ticket_id(ticket_id)
    
    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "comments": comments
    })

@app.post("/tickets/{ticket_id}/comment")
async def add_comment(
    request: Request,
    ticket_id: int,
    body: str = Form(...)
):
    """Add comment to ticket"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    user = get_user_by_id(int(user_id))
    add_comment_to_ticket(ticket_id, int(user_id), body)
    
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=302)

@app.post("/tickets/{ticket_id}/update")
async def update_ticket(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    assigned_to: Optional[int] = Form(None)
):
    """Update ticket status"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    update_ticket_status(ticket_id, status, assigned_to)
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=302)

# Analytics endpoints
@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics page"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    user = get_user_by_id(int(user_id))
    if user["role"] not in ["admin", "agent"]:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    monthly_data = get_monthly_analytics()
    yearly_data = get_yearly_analytics()
    repeat_tickets = get_repeat_tickets()
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "monthly_data": monthly_data,
        "yearly_data": yearly_data,
        "repeat_tickets": repeat_tickets
    })

# API endpoints
@app.get("/api/v1/tickets/", response_model=List[TicketOut])
def list_tickets_api(status: Optional[str] = None):
    """API endpoint for tickets"""
    tickets = get_tickets_by_status(status) if status else tickets_db
    return [enrich_ticket_data(ticket) for ticket in tickets]

@app.post("/api/v1/tickets/", response_model=TicketOut)
def create_ticket_api(ticket: TicketIn, request: Request):
    """API endpoint to create ticket"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    ticket_id = len(tickets_db) + 1
    new_ticket = {
        "id": ticket_id,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": "open",
        "created_by": int(user_id),
        "assigned_to": None,
        "created_at": datetime.now(),
        "updated_at": None,
        "tags": ticket.tags
    }
    tickets_db.append(new_ticket)
    return enrich_ticket_data(new_ticket)

# Helper functions
def get_dashboard_stats():
    """Get dashboard statistics"""
    total = len(tickets_db)
    open_count = len([t for t in tickets_db if t["status"] == "open"])
    in_progress_count = len([t for t in tickets_db if t["status"] == "in_progress"])
    resolved_count = len([t for t in tickets_db if t["status"] == "resolved"])
    closed_count = len([t for t in tickets_db if t["status"] == "closed"])
    
    return {
        "total_tickets": total,
        "open_tickets": open_count,
        "in_progress_tickets": in_progress_count,
        "resolved_tickets": resolved_count,
        "closed_tickets": closed_count,
        "monthly_tickets": len([t for t in tickets_db if t["created_at"].month == datetime.now().month]),
        "yearly_tickets": len([t for t in tickets_db if t["created_at"].year == datetime.now().year]),
        "repeat_tickets": len(analytics_db["repeat_tickets"])
    }

def get_recent_tickets():
    """Get recent tickets"""
    return sorted(tickets_db, key=lambda x: x["created_at"], reverse=True)[:10]

def get_tickets_by_status(status):
    """Get tickets by status"""
    if status == "all":
        return tickets_db
    return [t for t in tickets_db if t["status"] == status]

def get_ticket_by_id(ticket_id):
    """Get ticket by ID"""
    return next((t for t in tickets_db if t["id"] == ticket_id), None)

def get_user_by_id(user_id):
    """Get user by ID"""
    return next((u for u in users_db if u["id"] == user_id), None)

def get_comments_by_ticket_id(ticket_id):
    """Get comments for a ticket"""
    return [c for c in comments_db if c["ticket_id"] == ticket_id]

def add_comment_to_ticket(ticket_id, user_id, body):
    """Add comment to ticket"""
    comment_id = len(comments_db) + 1
    user = get_user_by_id(user_id)
    new_comment = {
        "id": comment_id,
        "ticket_id": ticket_id,
        "author_id": user_id,
        "author_name": user["full_name"],
        "body": body,
        "created_at": datetime.now()
    }
    comments_db.append(new_comment)

def update_ticket_status(ticket_id, status, assigned_to=None):
    """Update ticket status"""
    for ticket in tickets_db:
        if ticket["id"] == ticket_id:
            ticket["status"] = status
            ticket["updated_at"] = datetime.now()
            if assigned_to:
                ticket["assigned_to"] = assigned_to
            break

def enrich_ticket_data(ticket):
    """Enrich ticket data with user names"""
    created_by_user = get_user_by_id(ticket["created_by"])
    assigned_to_user = get_user_by_id(ticket["assigned_to"]) if ticket["assigned_to"] else None
    
    ticket["created_by_name"] = created_by_user["full_name"] if created_by_user else "Unknown"
    ticket["assigned_to_name"] = assigned_to_user["full_name"] if assigned_to_user else None
    
    return ticket

def get_monthly_analytics():
    """Get monthly analytics data"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_tickets = [t for t in tickets_db if t["created_at"].month == current_month and t["created_at"].year == current_year]
    
    return {
        "total": len(monthly_tickets),
        "by_status": {
            "open": len([t for t in monthly_tickets if t["status"] == "open"]),
            "in_progress": len([t for t in monthly_tickets if t["status"] == "in_progress"]),
            "resolved": len([t for t in monthly_tickets if t["status"] == "resolved"]),
            "closed": len([t for t in monthly_tickets if t["status"] == "closed"])
        },
        "by_priority": {
            "low": len([t for t in monthly_tickets if t["priority"] == "low"]),
            "medium": len([t for t in monthly_tickets if t["priority"] == "medium"]),
            "high": len([t for t in monthly_tickets if t["priority"] == "high"]),
            "urgent": len([t for t in monthly_tickets if t["priority"] == "urgent"])
        }
    }

def get_yearly_analytics():
    """Get yearly analytics data"""
    current_year = datetime.now().year
    yearly_tickets = [t for t in tickets_db if t["created_at"].year == current_year]
    
    return {
        "total": len(yearly_tickets),
        "by_month": {
            str(i): len([t for t in yearly_tickets if t["created_at"].month == i])
            for i in range(1, 13)
        }
    }

def get_repeat_tickets():
    """Get repeat tickets analysis"""
    # Simple implementation - in production, this would be more sophisticated
    return analytics_db["repeat_tickets"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
