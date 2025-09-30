from fastapi import APIRouter
from app.api.v1.endpoints import tickets, comments, summary

api_router = APIRouter()

api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(comments.router, prefix="/tickets", tags=["comments"])
api_router.include_router(summary.router, prefix="/summary", tags=["summary"])
