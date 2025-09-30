# QuickQueue - Project Structure

## Overview
Backend-focused FastAPI project for a Ticketing/Helpdesk Queue system with separate JSON APIs and web routes.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic settings configuration
│   │   ├── database.py         # SQLAlchemy engine, session, Base
│   │   ├── models.py           # SQLAlchemy 2.0 models (Ticket, Comment)
│   │   └── dependencies.py      # FastAPI dependencies (get_db, pagination)
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # Main API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── tickets.py    # Ticket CRUD endpoints
│   │           ├── comments.py    # Comment endpoints
│   │           └── summary.py     # Summary statistics
│   ├── web/
│   │   ├── __init__.py
│   │   └── routes.py           # Jinja2 web routes
│   └── schemas/
│       ├── __init__.py
│       └── ticket.py          # Pydantic v2 schemas
├── templates/                  # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   └── create.html
├── static/                    # Static files (empty)
├── tests/
│   ├── __init__.py
│   ├── test_api.py           # API endpoint tests
│   └── test_web.py           # Web route tests
├── alembic/                   # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── requirements.txt
└── README.md
```

## Key Components

### Core Module (`app/core/`)
- **config.py**: Pydantic settings with DATABASE_URL, SECRET_KEY, pagination settings
- **database.py**: SQLAlchemy engine, session factory, Base class, init_db()
- **models.py**: SQLAlchemy 2.0 models with proper indexes and relationships
- **dependencies.py**: FastAPI dependencies for database, pagination, authentication

### API Module (`app/api/v1/`)
- **tickets.py**: Full CRUD operations with filtering and pagination
- **comments.py**: Comment management for tickets
- **summary.py**: Statistics endpoints (counts by status/priority)

### Web Module (`app/web/`)
- **routes.py**: Minimal Jinja2 routes for HTML interface
- Separated from JSON APIs for clean architecture

### Data Models

#### Ticket Model
- `id` (PK), `title` (str, 160 chars), `description` (text)
- `priority` (enum: low|medium|high|urgent)
- `status` (enum: open|in_progress|resolved|closed)
- `created_at`, `updated_at` (datetime)
- `assigned_to` (nullable int, future use)
- Indexes on status, priority, created_at, and composite indexes

#### Comment Model
- `id` (PK), `ticket_id` (FK), `author` (str), `body` (text)
- `created_at` (datetime)
- Relationship with Ticket model

### API Endpoints

#### Tickets
- `POST /api/v1/tickets/` - Create ticket
- `GET /api/v1/tickets/` - List with filters (status, priority, search, pagination)
- `GET /api/v1/tickets/{id}` - Get ticket details
- `PATCH /api/v1/tickets/{id}` - Update ticket
- `DELETE /api/v1/tickets/{id}` - Delete ticket

#### Comments
- `POST /api/v1/tickets/{id}/comments` - Add comment
- `GET /api/v1/tickets/{id}/comments` - List comments (newest first)

#### Summary
- `GET /api/v1/summary/` - Statistics by status and priority

### Web Routes
- `GET /` - Home page (last 20 tickets)
- `GET /create` - Create ticket form
- `POST /create` - Handle form submission

## Development Setup

### Prerequisites
- Python 3.12+
- Virtual environment

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
```bash
# Initialize database
alembic upgrade head

# Create new migration (when models change)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Running the Application
```bash
# Development server
uvicorn app.main:app --reload --app-dir backend --port 8000

# Access points:
# - API: http://localhost:8000/api/v1/
# - Web: http://localhost:8000/
# - Docs: http://localhost:8000/docs
```

### Testing
```bash
# Run all tests
pytest -q backend

# Run specific test files
pytest backend/tests/test_api.py
pytest backend/tests/test_web.py
```

## Adding Features

### New API Endpoints
1. Create endpoint file in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/api.py`
3. Add tests in `tests/test_api.py`

### New Web Routes
1. Add routes to `app/web/routes.py`
2. Create templates in `templates/`
3. Add tests in `tests/test_web.py`

### Database Changes
1. Update models in `app/core/models.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`

### New Dependencies
1. Add to `requirements.txt`
2. Update `STRUCTURE.md` if needed

## Configuration

### Environment Variables
- `DATABASE_URL`: Database connection string (default: sqlite:///./quickqueue.db)
- `SECRET_KEY`: Secret key for security (change in production)
- `API_V1_STR`: API version prefix (default: /api/v1)

### Database Configuration
- SQLite for development
- PostgreSQL-ready (change DATABASE_URL)
- Alembic for migrations
- Proper indexes for performance

## Quality Standards

### Code Organization
- Separate concerns: API vs Web vs Core
- Dependency injection for database sessions
- Proper error handling with HTTPException
- Type hints throughout

### Testing
- Comprehensive API tests
- Web route tests
- Database fixtures
- Status code validation

### Documentation
- Clear module structure
- API documentation via FastAPI
- Setup and run instructions
- Feature addition guidelines
