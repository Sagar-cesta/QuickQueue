from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import Ticket

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Home page - show last 20 tickets"""
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(20).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tickets": tickets
    })


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    """Show create ticket form"""
    return templates.TemplateResponse("create.html", {"request": request})


@router.post("/create", response_class=HTMLResponse)
async def create_ticket(
    request: Request,
    title: str,
    description: str,
    priority: str,
    db: Session = Depends(get_db)
):
    """Handle create ticket form submission"""
    from app.core.models import Priority
    
    try:
        priority_enum = Priority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    ticket = Ticket(
        title=title,
        description=description,
        priority=priority_enum
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return templates.TemplateResponse("create.html", {
        "request": request,
        "success": f"Ticket #{ticket.id} created successfully!"
    })
