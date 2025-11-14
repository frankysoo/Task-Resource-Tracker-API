"""Task Pydantic schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for task creation."""
    pass


class TaskUpdate(BaseModel):
    """Schema for task updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskResponse(BaseModel):
    """Schema for task responses."""
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Task(BaseModel):
    """Complete task schema."""
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    status: TaskStatus
    priority: TaskPriority
    assigned_to_id: Optional[int]
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskFilter(BaseModel):
    """Schema for task filtering."""
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    project_id: Optional[int] = None
    priority: Optional[str] = None
    due_before: Optional[str] = None
    due_after: Optional[str] = None
    search: Optional[str] = None