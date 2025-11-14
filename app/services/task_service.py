"""Task service for handling task-related operations."""

from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter


class TaskService:
    """Service for handling task operations."""
    
    @staticmethod
    def create_task(db: Session, task_create: TaskCreate, user_id: int) -> Task:
        """Create a new task."""
        db_task = Task(**task_create.model_dump())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def get_tasks(
        db: Session, 
        filters: Optional[TaskFilter] = None,
        user_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Task]:
        """Get tasks with optional filtering."""
        query = db.query(Task)
        
        if filters:
            if filters.status:
                try:
                    status_enum = TaskStatus(filters.status)
                    query = query.filter(Task.status == status_enum)
                except ValueError:
                    pass  # Invalid status, ignore filter
            if filters.assigned_to:
                query = query.filter(Task.assigned_to_id == filters.assigned_to)
            if filters.project_id:
                query = query.filter(Task.project_id == filters.project_id)
            if filters.priority:
                try:
                    priority_enum = TaskPriority(filters.priority)
                    query = query.filter(Task.priority == priority_enum)
                except ValueError:
                    pass  # Invalid priority, ignore filter
            if filters.due_before:
                try:
                    from datetime import datetime
                    due_before_date = datetime.strptime(filters.due_before, "%Y-%m-%d").date()
                    query = query.filter(Task.due_date <= due_before_date)
                except ValueError:
                    pass  # Invalid date format, ignore filter
            if filters.due_after:
                try:
                    from datetime import datetime
                    due_after_date = datetime.strptime(filters.due_after, "%Y-%m-%d").date()
                    query = query.filter(Task.due_date >= due_after_date)
                except ValueError:
                    pass  # Invalid date format, ignore filter
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term)
                    )
                )
        
        if user_id:
            query = query.filter(
                or_(
                    Task.assigned_to_id == user_id,
                    Task.project.has(owner_id=user_id)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """Update task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """Delete task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        db.delete(task)
        db.commit()
        return True
    
    @staticmethod
    def get_overdue_tasks(db: Session) -> List[Task]:
        """Get all overdue tasks."""
        from datetime import date
        
        return db.query(Task).filter(
            Task.due_date < date.today(),
            Task.status != TaskStatus.DONE
        ).all()
    
    @staticmethod
    def get_completion_stats(db: Session) -> dict:
        """Get task completion statistics."""
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.DONE).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        
        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }