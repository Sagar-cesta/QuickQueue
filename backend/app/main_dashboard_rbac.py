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

# Import our enhanced auth system
from app.core.auth import (
    authenticate_user, create_access_token, get_current_user_from_session,
    require_login, require_role, require_permission_web, has_permission,
    get_all_users, create_user, update_user_role, delete_user, get_user_permissions
)

# Enhanced in-memory storage for demo purposes
tickets_db = []
comments_db = []
analytics_db = {
    "monthly_metrics": {},
    "yearly_metrics": {},
    "repeat_tickets": []
}

# Initialize with sample data
def init_sample_data():
    """Initialize with sample data for demo"""
    global tickets_db
    
    # Sample tickets
    tickets_db.extend([
        {
            "id": 1, "title": "Login Issue", "description": "Cannot login to the system",
            "priority": "high", "status": "open", "created_by": "user", "created_by_name": "Regular User",
            "created_at": datetime.now() - timedelta(days=2), "updated_at": datetime.now() - timedelta(days=1),
            "assigned_to": None, "is_repeat": False, "tags": ["login", "authentication"]
        },
        {
            "id": 2, "title": "Database Connection Error", "description": "Database connection timeout",
            "priority": "urgent", "status": "in_progress", "created_by": "admin", "created_by_name": "System Administrator",
            "created_at": datetime.now() - timedelta(days=1), "updated_at": datetime.now() - timedelta(hours=2),
            "assigned_to": "agent", "is_repeat": False, "tags": ["database", "connection"]
        },
        {
            "id": 3, "title": "UI Bug in Dashboard", "description": "Charts not displaying correctly",
            "priority": "medium", "status": "resolved", "created_by": "user", "created_by_name": "Regular User",
            "created_at": datetime.now() - timedelta(days=3), "updated_at": datetime.now() - timedelta(hours=1),
            "assigned_to": "agent", "is_repeat": True, "tags": ["ui", "dashboard", "charts"]
        },
        {
            "id": 4, "title": "Performance Issue", "description": "System running slowly",
            "priority": "high", "status": "closed", "created_by": "user", "created_by_name": "Regular User",
            "created_at": datetime.now() - timedelta(days=5), "updated_at": datetime.now() - timedelta(days=1),
            "assigned_to": "agent", "is_repeat": False, "tags": ["performance", "optimization"]
        },
        {
            "id": 5, "title": "Email Notifications Not Working", "description": "Users not receiving email notifications",
            "priority": "medium", "status": "open", "created_by": "user", "created_by_name": "Regular User",
            "created_at": datetime.now() - timedelta(hours=6), "updated_at": datetime.now() - timedelta(hours=6),
            "assigned_to": None, "is_repeat": False, "tags": ["email", "notifications"]
        },
        {
            "id": 6, "title": "Mobile App Crash", "description": "App crashes when opening ticket details",
            "priority": "urgent", "status": "in_progress", "created_by": "agent", "created_by_name": "Support Agent",
            "created_at": datetime.now() - timedelta(hours=3), "updated_at": datetime.now() - timedelta(hours=1),
            "assigned_to": "agent", "is_repeat": False, "tags": ["mobile", "crash", "app"]
        }
    ])
    
    # Sample comments
    comments_db.extend([
        {
            "id": 1, "ticket_id": 2, "author": "agent", "author_name": "Support Agent",
            "body": "Working on the database connection issue. Found the root cause.",
            "created_at": datetime.now() - timedelta(hours=3)
        },
        {
            "id": 2, "ticket_id": 3, "author": "agent", "author_name": "Support Agent",
            "body": "Fixed the chart rendering issue. The problem was with the Chart.js configuration.",
            "created_at": datetime.now() - timedelta(hours=2)
        },
        {
            "id": 3, "ticket_id": 1, "author": "user", "author_name": "Regular User",
            "body": "I'm still experiencing login issues. Can you please help?",
            "created_at": datetime.now() - timedelta(hours=1)
        },
        {
            "id": 4, "ticket_id": 4, "author": "agent", "author_name": "Support Agent",
            "body": "Performance issue has been resolved. System is now running smoothly.",
            "created_at": datetime.now() - timedelta(days=1)
        }
    ])

# Initialize sample data
init_sample_data()

app = FastAPI(title="QuickQueue Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Pydantic models
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str
    tags: Optional[str] = ""

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    is_repeat: Optional[bool] = None

class CommentCreate(BaseModel):
    body: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Helper functions
def get_ticket_stats():
    """Get ticket statistics"""
    total = len(tickets_db)
    open_count = len([t for t in tickets_db if t["status"] == "open"])
    in_progress_count = len([t for t in tickets_db if t["status"] == "in_progress"])
    resolved_count = len([t for t in tickets_db if t["status"] == "resolved"])
    closed_count = len([t for t in tickets_db if t["status"] == "closed"])
    
    # Monthly and yearly stats
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_tickets = len([t for t in tickets_db if t["created_at"].month == current_month])
    yearly_tickets = len([t for t in tickets_db if t["created_at"].year == current_year])
    repeat_tickets = len([t for t in tickets_db if t["is_repeat"]])
    
    return {
        "total_tickets": total,
        "open_tickets": open_count,
        "in_progress_tickets": in_progress_count,
        "resolved_tickets": resolved_count,
        "closed_tickets": closed_count,
        "monthly_tickets": monthly_tickets,
        "yearly_tickets": yearly_tickets,
        "repeat_tickets": repeat_tickets
    }

def get_recent_tickets(limit: int = 5):
    """Get recent tickets"""
    return sorted(tickets_db, key=lambda x: x["created_at"], reverse=True)[:limit]

def get_analytics_data():
    """Get analytics data"""
    # Monthly data
    monthly_data = {
        "by_status": {
            "open": len([t for t in tickets_db if t["status"] == "open" and t["created_at"].month == datetime.now().month]),
            "in_progress": len([t for t in tickets_db if t["status"] == "in_progress" and t["created_at"].month == datetime.now().month]),
            "resolved": len([t for t in tickets_db if t["status"] == "resolved" and t["created_at"].month == datetime.now().month]),
            "closed": len([t for t in tickets_db if t["status"] == "closed" and t["created_at"].month == datetime.now().month])
        },
        "by_priority": {
            "low": len([t for t in tickets_db if t["priority"] == "low" and t["created_at"].month == datetime.now().month]),
            "medium": len([t for t in tickets_db if t["priority"] == "medium" and t["created_at"].month == datetime.now().month]),
            "high": len([t for t in tickets_db if t["priority"] == "high" and t["created_at"].month == datetime.now().month]),
            "urgent": len([t for t in tickets_db if t["priority"] == "urgent" and t["created_at"].month == datetime.now().month])
        }
    }
    
    # Yearly data
    yearly_data = {
        "by_month": {}
    }
    for month in range(1, 13):
        yearly_data["by_month"][str(month)] = len([t for t in tickets_db if t["created_at"].month == month and t["created_at"].year == datetime.now().year])
    
    return monthly_data, yearly_data

# Root route
@app.get("/")
async def root():
    """Root route - redirect to login"""
    return RedirectResponse(url="/login", status_code=302)

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    
    # Set session cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="username", value=user["username"], httponly=True)
    response.set_cookie(key="user_role", value=user["role"], httponly=True)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    
    return response

@app.get("/logout")
async def logout():
    """Handle logout"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="username")
    response.delete_cookie(key="user_role")
    response.delete_cookie(key="access_token")
    return response

# Dashboard routes
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(require_permission_web("can_view_dashboard"))):
    """Dashboard page"""
    stats = get_ticket_stats()
    recent_tickets = get_recent_tickets()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_tickets": recent_tickets,
        "user": current_user
    })

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request, status: Optional[str] = None):
    """Tickets page"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Filter tickets based on user role
    if current_user["role"] == "user":
        # Users can only see their own tickets
        filtered_tickets = [t for t in tickets_db if t["created_by"] == current_user["username"]]
    else:
        # Admin and agents can see all tickets
        filtered_tickets = tickets_db.copy()
    
    # Apply status filter
    if status:
        filtered_tickets = [t for t in filtered_tickets if t["status"] == status]
    
    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "tickets": filtered_tickets,
        "current_status": status or "all",
        "user": current_user
    })

@app.get("/tickets/create", response_class=HTMLResponse)
async def create_ticket_page(request: Request):
    """Create ticket page"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("create_ticket.html", {
        "request": request,
        "user": current_user
    })

@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_id: int):
    """Ticket detail page"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if user can view this ticket
    if current_user["role"] == "user" and ticket["created_by"] != current_user["username"]:
        # Return access denied template instead of raising exception
        return templates.TemplateResponse("access_denied.html", {
            "request": request,
            "user": current_user
        })
    
    # Get comments for this ticket
    ticket_comments = [c for c in comments_db if c["ticket_id"] == ticket_id]
    
    return templates.TemplateResponse("ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "comments": ticket_comments,
        "user": current_user
    })

@app.post("/tickets/create")
async def create_ticket(request: Request):
    """Create new ticket"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    form_data = await request.form()
    
    # Create new ticket
    new_ticket = {
        "id": max([t["id"] for t in tickets_db], default=0) + 1,
        "title": form_data["title"],
        "description": form_data["description"],
        "priority": form_data["priority"],
        "status": "open",
        "created_by": current_user["username"],
        "created_by_name": current_user["full_name"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "assigned_to": None,
        "is_repeat": False,
        "tags": form_data.get("tags", "").split(",") if form_data.get("tags") else []
    }
    
    tickets_db.append(new_ticket)
    
    return RedirectResponse(url="/tickets", status_code=302)

@app.post("/tickets/{ticket_id}/delete")
async def delete_ticket(request: Request, ticket_id: int):
    """Delete ticket"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if user can delete this ticket
    if current_user["role"] == "user" and ticket["created_by"] != current_user["username"]:
        return templates.TemplateResponse("access_denied.html", {
            "request": request,
            "user": current_user
        })
    
    # Only admin can delete tickets
    if current_user["role"] != "admin":
        return templates.TemplateResponse("access_denied.html", {
            "request": request,
            "user": current_user
        })
    
    # Remove ticket
    tickets_db.remove(ticket)
    
    return RedirectResponse(url="/tickets", status_code=302)

@app.post("/tickets/{ticket_id}/update")
async def update_ticket(request: Request, ticket_id: int):
    """Update ticket"""
    # Check authentication
    current_user = get_current_user_from_session(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if user can edit this ticket
    if current_user["role"] == "user" and ticket["created_by"] != current_user["username"]:
        return templates.TemplateResponse("access_denied.html", {
            "request": request,
            "user": current_user
        })
    
    form_data = await request.form()
    
    # Update ticket based on user role
    if current_user["role"] == "admin":
        # Admin can update everything
        if "title" in form_data:
            ticket["title"] = form_data["title"]
        if "description" in form_data:
            ticket["description"] = form_data["description"]
        if "priority" in form_data:
            ticket["priority"] = form_data["priority"]
        if "status" in form_data:
            ticket["status"] = form_data["status"]
        if "assigned_to" in form_data:
            ticket["assigned_to"] = form_data["assigned_to"]
        if "is_repeat" in form_data:
            ticket["is_repeat"] = form_data["is_repeat"] == "on"
    
    elif current_user["role"] == "agent":
        # Agents can close, resolve, and mark as repeat
        if "status" in form_data and form_data["status"] in ["closed", "resolved"]:
            ticket["status"] = form_data["status"]
        if "is_repeat" in form_data:
            ticket["is_repeat"] = form_data["is_repeat"] == "on"
        if "assigned_to" in form_data:
            ticket["assigned_to"] = form_data["assigned_to"]
    
    elif current_user["role"] == "user":
        # Users can only resolve their own tickets
        if ticket["created_by"] == current_user["username"] and "status" in form_data and form_data["status"] == "resolved":
            ticket["status"] = "resolved"
    
    ticket["updated_at"] = datetime.now()
    
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=302)

@app.post("/tickets/{ticket_id}/comment")
async def add_comment(request: Request, ticket_id: int, current_user: dict = Depends(require_permission_web("can_resolve_tickets"))):
    """Add comment to ticket"""
    ticket = next((t for t in tickets_db if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if user can comment on this ticket
    if current_user["role"] == "user" and ticket["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    form_data = await request.form()
    comment_body = form_data.get("body", "")
    
    if comment_body:
        new_comment = {
            "id": len(comments_db) + 1,
            "ticket_id": ticket_id,
            "author": current_user["username"],
            "author_name": current_user["full_name"],
            "body": comment_body,
            "created_at": datetime.now()
        }
        comments_db.append(new_comment)
    
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=302)

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, current_user: dict = Depends(require_permission_web("can_view_analytics"))):
    """Analytics page"""
    monthly_data, yearly_data = get_analytics_data()
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "monthly_data": monthly_data,
        "yearly_data": yearly_data,
        "user": current_user
    })

# User management routes (Admin only)
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, current_user: dict = Depends(require_permission_web("can_create_users"))):
    """Users management page"""
    users = get_all_users()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "user": current_user
    })

@app.post("/users/create")
async def create_user_endpoint(request: Request, current_user: dict = Depends(require_permission_web("can_create_users"))):
    """Create new user"""
    form_data = await request.form()
    
    try:
        new_user = create_user(
            username=form_data["username"],
            password=form_data["password"],
            role=form_data["role"],
            full_name=form_data["full_name"],
            email=form_data["email"]
        )
        return RedirectResponse(url="/users?success=User created successfully", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/users?error={str(e)}", status_code=302)

@app.post("/users/{username}/update")
async def update_user_endpoint(request: Request, username: str, current_user: dict = Depends(require_permission_web("can_edit_users"))):
    """Update user"""
    form_data = await request.form()
    
    try:
        if "role" in form_data:
            update_user_role(username, form_data["role"])
        return RedirectResponse(url="/users?success=User updated successfully", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/users?error={str(e)}", status_code=302)

@app.post("/users/{username}/delete")
async def delete_user_endpoint(request: Request, username: str, current_user: dict = Depends(require_permission_web("can_delete_users"))):
    """Delete user"""
    try:
        delete_user(username)
        return RedirectResponse(url="/users?success=User deleted successfully", status_code=302)
    except ValueError as e:
        return RedirectResponse(url=f"/users?error={str(e)}", status_code=302)

# API routes for AJAX calls
@app.get("/api/stats")
async def get_stats(current_user: dict = Depends(require_permission_web("can_view_dashboard"))):
    """Get statistics API"""
    return get_ticket_stats()

@app.get("/api/tickets")
async def get_tickets_api(status: Optional[str] = None, current_user: dict = Depends(require_permission_web("can_view_all_tickets"))):
    """Get tickets API"""
    # Filter tickets based on user role
    if current_user["role"] == "user":
        filtered_tickets = [t for t in tickets_db if t["created_by"] == current_user["username"]]
    else:
        filtered_tickets = tickets_db.copy()
    
    if status:
        filtered_tickets = [t for t in filtered_tickets if t["status"] == status]
    
    return {"tickets": filtered_tickets}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
