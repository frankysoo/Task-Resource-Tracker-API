# Task & Resource Tracker API

A FastAPI-based backend for managing tasks and projects with JWT authentication and role-based access control.

## Features

- JWT-based authentication with role management
- Full CRUD operations for tasks and projects
- User registration and profile management
- Advanced filtering and search capabilities
- Comprehensive reporting for admins
- Auto-generated API documentation
- Docker support for easy deployment

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: SQLite (default) or PostgreSQL
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens
- **Testing**: pytest with HTTPX

## Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`.

### Docker

Build and run with Docker Compose:
```bash
docker-compose up --build
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/refresh` - Refresh access token

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile

### Projects
- `POST /projects/` - Create new project
- `GET /projects/` - List user's projects
- `GET /projects/{id}` - Get project by ID
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Tasks
- `POST /tasks/` - Create new task
- `GET /tasks/` - List tasks with filtering
- `GET /tasks/{id}` - Get task by ID
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

### Reports (Admin Only)
- `GET /reports/completion` - Task completion statistics
- `GET /reports/overdue` - Overdue tasks

### Health Check
- `GET /health` - API health check

## Testing

Run the test suite:
```bash
pytest app/tests/ -v
```

## Deployment

The application can be deployed to platforms like Render or Railway. Set environment variables as needed:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Secret key for JWT signing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
