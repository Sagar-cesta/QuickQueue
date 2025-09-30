# QuickQueue - Ticketing/Helpdesk Queue System

A backend-focused FastAPI application for managing support tickets with separate JSON APIs and web interfaces.

## Features

- **RESTful API** with full CRUD operations for tickets and comments
- **Web Interface** with Jinja2 templates for ticket management
- **Database Integration** with SQLAlchemy 2.0 and Alembic migrations
- **Comprehensive Testing** with pytest
- **Filtering & Pagination** for efficient data handling
- **Statistics Dashboard** with ticket counts by status and priority

## Quick Start

### Prerequisites
- Python 3.12+
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --app-dir backend --port 8000
   ```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:8000/
- **API Base**: http://localhost:8000/api/v1/

## API Endpoints

### Tickets
- `POST /api/v1/tickets/` - Create a new ticket
- `GET /api/v1/tickets/` - List tickets (with filters and pagination)
- `GET /api/v1/tickets/{id}` - Get ticket details
- `PATCH /api/v1/tickets/{id}` - Update ticket
- `DELETE /api/v1/tickets/{id}` - Delete ticket

### Comments
- `POST /api/v1/tickets/{id}/comments` - Add comment to ticket
- `GET /api/v1/tickets/{id}/comments` - List ticket comments

### Summary
- `GET /api/v1/summary/` - Get ticket statistics

## Web Interface

- **Home** (`/`) - View recent tickets
- **Create Ticket** (`/create`) - Simple form to create tickets

## Testing

Run the test suite:
```bash
pytest -q backend
```

Run specific test files:
```bash
pytest backend/tests/test_api.py
pytest backend/tests/test_web.py
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Configuration

The application uses environment variables for configuration:

- `DATABASE_URL`: Database connection string (default: `sqlite:///./quickqueue.db`)
- `SECRET_KEY`: Secret key for security
- `API_V1_STR`: API version prefix (default: `/api/v1`)

Create a `.env` file to override defaults:
```env
DATABASE_URL=postgresql://user:password@localhost/quickqueue
SECRET_KEY=your-secret-key-here
```

## Project Structure

See [STRUCTURE.md](STRUCTURE.md) for detailed project organization and development guidelines.

## Development

### Adding New Features

1. **API Endpoints**: Add to `app/api/v1/endpoints/`
2. **Web Routes**: Add to `app/web/routes.py`
3. **Database Models**: Update `app/core/models.py`
4. **Tests**: Add to `tests/` directory

### Code Quality

- Type hints throughout
- Comprehensive error handling
- Proper HTTP status codes
- Database indexes for performance
- Separation of concerns (API vs Web)

## Production Deployment

For production deployment:

1. Use PostgreSQL instead of SQLite
2. Set secure `SECRET_KEY`
3. Configure proper CORS settings
4. Use environment variables for all configuration
5. Set up proper logging
6. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)

## License

This project is for educational and development purposes.
