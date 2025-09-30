import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core.models import Ticket, Priority, Status

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_home_page(db_session):
    """Test home page returns 200 and contains Recent Tickets"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Recent Tickets" in response.text

def test_create_form(db_session):
    """Test create form page"""
    response = client.get("/create")
    assert response.status_code == 200
    assert "Create New Ticket" in response.text

def test_create_ticket_form(db_session):
    """Test creating ticket via form"""
    response = client.post("/create", data={
        "title": "Test Ticket",
        "description": "Test description",
        "priority": "high"
    })
    assert response.status_code == 200
    assert "Ticket #" in response.text
    assert "created successfully" in response.text
