from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.web.routes import router as web_router

# Initialize database
init_db()

app = FastAPI(
    title=settings.project_name,
    description="Ticketing/Helpdesk Queue System",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api_router, prefix=settings.api_v1_str)
app.include_router(web_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
