import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core.models import Ticket, Comment, Priority, Status

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

def test_create_ticket(db_session):
    """Test creating a ticket"""
    response = client.post("/api/v1/tickets/", json={
        "title": "Test Ticket",
        "description": "This is a test ticket",
        "priority": "high"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Ticket"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert "id" in data

def test_list_tickets(db_session):
    """Test listing tickets"""
    # Create a test ticket
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    response = client.get("/api/v1/tickets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test"

def test_get_ticket(db_session):
    """Test getting a specific ticket"""
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    response = client.get(f"/api/v1/tickets/{ticket.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test"

def test_update_ticket(db_session):
    """Test updating a ticket"""
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    response = client.patch(f"/api/v1/tickets/{ticket.id}", json={
        "status": "in_progress",
        "priority": "urgent"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "urgent"

def test_delete_ticket(db_session):
    """Test deleting a ticket"""
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    response = client.delete(f"/api/v1/tickets/{ticket.id}")
    assert response.status_code == 204

def test_add_comment(db_session):
    """Test adding a comment"""
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    response = client.post(f"/api/v1/tickets/{ticket.id}/comments", json={
        "author": "Test User",
        "body": "This is a test comment"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["author"] == "Test User"
    assert data["body"] == "This is a test comment"

def test_list_comments(db_session):
    """Test listing comments"""
    ticket = Ticket(title="Test", description="Test desc", priority=Priority.MEDIUM)
    db_session.add(ticket)
    db_session.commit()
    
    comment = Comment(ticket_id=ticket.id, author="Test User", body="Test comment")
    db_session.add(comment)
    db_session.commit()
    
    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["author"] == "Test User"

def test_summary(db_session):
    """Test summary endpoint"""
    # Create tickets with different statuses and priorities
    tickets = [
        Ticket(title="Open High", description="Test", priority=Priority.HIGH, status=Status.OPEN),
        Ticket(title="In Progress Medium", description="Test", priority=Priority.MEDIUM, status=Status.IN_PROGRESS),
        Ticket(title="Resolved Low", description="Test", priority=Priority.LOW, status=Status.RESOLVED),
    ]
    for ticket in tickets:
        db_session.add(ticket)
    db_session.commit()
    
    response = client.get("/api/v1/summary/")
    assert response.status_code == 200
    data = response.json()
    assert "by_status" in data
    assert "by_priority" in data
    assert data["by_status"]["open"] == 1
    assert data["by_priority"]["high"] == 1
