"""Main FastAPI application. This is where everything starts!"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.database import Base
from app.routers import auth_router, users_router, projects_router, tasks_router, reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown. Kinda like init and cleanup."""
    # Startup stuff
    print("Starting up the server...")
    # Make sure all database tables exist
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup when shutting down
    print("Server is shutting down...")


# Create the main FastAPI app - this is the heart of everything!
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="My task tracking API that I built for learning",
    lifespan=lifespan
)

# CORS setup - allows frontend to talk to backend
# TODO: Make this more secure for production, don't allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This is not secure, but works for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hook up all the different parts of the API
app.include_router(auth_router)  # Login/signup stuff
app.include_router(users_router)  # User management
app.include_router(projects_router)  # Projects
app.include_router(tasks_router)  # Tasks
app.include_router(reports_router)  # Reports for admins


@app.get("/")
async def root():
    """Basic welcome page that shows API info."""
    return {
        "message": "Welcome to my Task Tracker API!",
        "version": "1.0.0",
        "docs": "/docs",  # Swagger docs
        "redoc": "/redoc"  # Alternative docs
    }


@app.get("/health")
async def health_check():
    """Simple health check so we know the server is running."""
    return {"status": "healthy", "service": settings.app_name}
