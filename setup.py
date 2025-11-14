#!/usr/bin/env python3
"""Setup script for Task & Resource Tracker API."""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole


def setup_database():
    """Set up the database with initial schema."""
    print("Setting up database...")
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")


def create_admin_user():
    """Create an admin user if it doesn't exist."""
    print("Creating admin user...")
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Check if admin user exists
    admin_user = db.query(User).filter(User.email == "admin@tasktracker.com").first()
    
    if not admin_user:
        # Create admin user
        admin_user = User(
            email="admin@tasktracker.com",
            name="Administrator",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully!")
        print("Email: admin@tasktracker.com")
        print("Password: admin123")
    else:
        print("Admin user already exists.")
    
    db.close()


def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data...")
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Create sample users
    from app.models.project import Project
    from app.models.task import Task, TaskStatus, TaskPriority
    from datetime import date, timedelta
    
    # Create sample user
    sample_user = db.query(User).filter(User.email == "user@tasktracker.com").first()
    if not sample_user:
        sample_user = User(
            email="user@tasktracker.com",
            name="Sample User",
            password_hash=get_password_hash("user123"),
            role=UserRole.USER,
            is_active=True
        )
        db.add(sample_user)
        db.commit()
        print("Sample user created: user@tasktracker.com / user123")
    
    # Create sample project
    sample_project = Project(
        name="Sample Project",
        description="A sample project for demonstration",
        owner_id=sample_user.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30)
    )
    db.add(sample_project)
    db.commit()
    
    # Create sample tasks
    tasks = [
        Task(
            title="Complete project setup",
            description="Set up the initial project structure",
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
            assigned_to_id=sample_user.id,
            project_id=sample_project.id,
            due_date=date.today() - timedelta(days=1)
        ),
        Task(
            title="Implement authentication",
            description="Add JWT authentication to the API",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assigned_to_id=sample_user.id,
            project_id=sample_project.id,
            due_date=date.today() + timedelta(days=3)
        ),
        Task(
            title="Write documentation",
            description="Create comprehensive API documentation",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            assigned_to_id=sample_user.id,
            project_id=sample_project.id,
            due_date=date.today() + timedelta(days=7)
        ),
        Task(
            title="Add unit tests",
            description="Write comprehensive unit tests for all endpoints",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            assigned_to_id=sample_user.id,
            project_id=sample_project.id,
            due_date=date.today() + timedelta(days=14)
        )
    ]
    
    for task in tasks:
        db.add(task)
    
    db.commit()
    print("Sample data created successfully!")
    db.close()


def main():
    """Main setup function."""
    print("Task & Resource Tracker API Setup")
    print("=" * 50)
    
    try:
        setup_database()
        create_admin_user()
        create_sample_data()
        
        print("\nSetup completed successfully!")
        print("\nYou can now start the application with:")
        print("uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()