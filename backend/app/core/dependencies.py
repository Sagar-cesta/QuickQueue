from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.config import settings


def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size, description="Items per page")
):
    """Pagination dependency"""
    return {"page": page, "page_size": page_size}


def get_current_user():
    """Stub for future user authentication"""
    # This would normally validate JWT token and return user
    return {"id": 1, "username": "admin"}  # Stub user
