"""Project service for handling project-related operations."""

from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for handling project operations."""
    
    @staticmethod
    def create_project(db: Session, project_create: ProjectCreate, owner_id: int) -> Project:
        """Create a new project."""
        db_project = Project(**project_create.model_dump(), owner_id=owner_id)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_projects(
        db: Session, 
        owner_id: Optional[int] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Project]:
        """Get projects with optional owner filter."""
        query = db.query(Project)
        
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_project(
        db: Session, 
        project_id: int, 
        project_update: ProjectUpdate, 
        user_id: int
    ) -> Optional[Project]:
        """Update project (only by owner)."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == user_id
        ).first()
        
        if not project:
            return None
        
        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int, user_id: int) -> bool:
        """Delete project (only by owner)."""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == user_id
        ).first()
        
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        return True
    
    @staticmethod
    def get_projects_with_stats(
        db: Session, 
        owner_id: Optional[int] = None
    ) -> List[Project]:
        """Get projects with task count statistics."""
        query = db.query(Project).outerjoin(Task).group_by(Project.id).add_column(
            func.count(Task.id).label('task_count')
        )
        
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        
        results = query.all()
        projects = []
        for project, task_count in results:
            project.task_count = task_count
            projects.append(project)
        
        return projects