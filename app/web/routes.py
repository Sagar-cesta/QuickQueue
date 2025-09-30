from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    """Tickets management page"""
    return templates.TemplateResponse("tickets.html", {"request": request})
