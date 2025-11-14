"""Reporting routes."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.task import TaskStatus
from app.routers.auth import get_current_active_user
from app.services.task_service import TaskService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get admin user for admin-only endpoints."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


@router.get("/completion", response_model=Dict)
def get_completion_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get task completion statistics (admin only)."""
    stats = TaskService.get_completion_stats(db)
    return stats


@router.get("/overdue", response_model=List[Dict])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get all overdue tasks (admin only)."""
    from app.schemas.task import TaskResponse
    
    tasks = TaskService.get_overdue_tasks(db)
    return [TaskResponse.model_validate(task).model_dump() for task in tasks]


@router.get("/projects", response_model=Dict)
def get_project_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get project statistics (admin only)."""
    from app.models.project import Project
    from app.models.task import Task
    from sqlalchemy import func
    
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(
        Project.tasks.any(Task.status != TaskStatus.DONE)
    ).count()
    
    completed_projects = db.query(Project).filter(
        ~Project.tasks.any(Task.status != TaskStatus.DONE),
        Project.tasks.any()
    ).count()
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "projects_with_tasks": db.query(Project).filter(Project.tasks.any()).count()
    }