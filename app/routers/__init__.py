"""API routers package."""

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.reports import router as reports_router

__all__ = ["auth_router", "users_router", "projects_router", "tasks_router", "reports_router"]