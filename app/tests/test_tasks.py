"""Tests for task management endpoints."""

import pytest
from fastapi import status
from datetime import date, timedelta


class TestCreateTask:
    """Test task creation."""

    def test_create_task_success(self, client, auth_headers, test_user):
        """Test successfully creating a task."""
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": "Test Task",
                "description": "A test task description",
                "status": "pending",
                "priority": "high",
                "due_date": str(date.today() + timedelta(days=7))
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task description"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["assigned_to_id"] == test_user.id

    def test_create_task_minimal(self, client, auth_headers):
        """Test creating task with minimal data."""
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={"title": "Minimal Task"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    def test_create_task_with_project(self, client, auth_headers, test_user, db):
        """Test creating task associated with project."""
        from app.models.project import Project
        
        project = Project(name="Test Project", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": "Project Task",
                "project_id": project.id
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["project_id"] == project.id

    def test_create_task_unauthorized(self, client):
        """Test creating task without authentication."""
        response = client.post(
            "/tasks/",
            json={"title": "Test Task"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListTasks:
    """Test listing tasks."""

    def test_list_tasks_success(self, client, auth_headers, test_user, db):
        """Test successfully listing user's tasks."""
        from app.models.task import Task
        
        task1 = Task(title="Task 1", assigned_to_id=test_user.id)
        task2 = Task(title="Task 2", assigned_to_id=test_user.id)
        db.add_all([task1, task2])
        db.commit()
        
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_tasks_filter_by_status(self, client, auth_headers, test_user, db):
        """Test filtering tasks by status."""
        from app.models.task import Task, TaskStatus
        
        task1 = Task(title="Pending Task", assigned_to_id=test_user.id, status=TaskStatus.PENDING)
        task2 = Task(title="Done Task", assigned_to_id=test_user.id, status=TaskStatus.DONE)
        db.add_all([task1, task2])
        db.commit()
        
        response = client.get("/tasks/?status=done", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for task in data:
            assert task["status"] == "done"

    def test_list_tasks_filter_by_priority(self, client, auth_headers, test_user, db):
        """Test filtering tasks by priority."""
        from app.models.task import Task, TaskPriority
        
        task1 = Task(title="High Priority", assigned_to_id=test_user.id, priority=TaskPriority.HIGH)
        task2 = Task(title="Low Priority", assigned_to_id=test_user.id, priority=TaskPriority.LOW)
        db.add_all([task1, task2])
        db.commit()
        
        response = client.get("/tasks/?priority=high", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for task in data:
            assert task["priority"] == "high"

    def test_list_tasks_filter_by_project(self, client, auth_headers, test_user, db):
        """Test filtering tasks by project."""
        from app.models.project import Project
        from app.models.task import Task
        
        project = Project(name="Test Project", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        task1 = Task(title="Project Task", assigned_to_id=test_user.id, project_id=project.id)
        task2 = Task(title="No Project Task", assigned_to_id=test_user.id)
        db.add_all([task1, task2])
        db.commit()
        
        response = client.get(f"/tasks/?project_id={project.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for task in data:
            assert task["project_id"] == project.id

    def test_list_tasks_search(self, client, auth_headers, test_user, db):
        """Test searching tasks by text."""
        from app.models.task import Task
        
        task1 = Task(title="Important Meeting", description="Discuss project", assigned_to_id=test_user.id)
        task2 = Task(title="Code Review", description="Review PRs", assigned_to_id=test_user.id)
        db.add_all([task1, task2])
        db.commit()
        
        response = client.get("/tasks/?search=meeting", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any("meeting" in task["title"].lower() for task in data)

    def test_list_tasks_pagination(self, client, auth_headers, test_user, db):
        """Test task listing pagination."""
        from app.models.task import Task
        
        for i in range(10):
            task = Task(title=f"Task {i}", assigned_to_id=test_user.id)
            db.add(task)
        db.commit()
        
        response = client.get("/tasks/?skip=0&limit=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5


class TestGetTask:
    """Test getting single task."""

    def test_get_task_success(self, client, auth_headers, test_user, db):
        """Test successfully getting a task."""
        from app.models.task import Task
        
        task = Task(
            title="Test Task",
            description="Test description",
            assigned_to_id=test_user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.get(f"/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "Test Task"

    def test_get_task_not_found(self, client, auth_headers):
        """Test getting nonexistent task."""
        response = client.get("/tasks/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task_not_authorized(self, client, auth_headers, admin_user, db):
        """Test getting task not assigned to user."""
        from app.models.task import Task
        
        task = Task(title="Admin Task", assigned_to_id=admin_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.get(f"/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_project_task_as_owner(self, client, auth_headers, test_user, admin_user, db):
        """Test project owner can access project tasks."""
        from app.models.project import Project
        from app.models.task import Task
        
        # Create project owned by test_user
        project = Project(name="Test Project", owner_id=test_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create task in project assigned to admin
        task = Task(
            title="Project Task",
            project_id=project.id,
            assigned_to_id=admin_user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Test user (project owner) should be able to access
        response = client.get(f"/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestUpdateTask:
    """Test updating tasks."""

    def test_update_task_success(self, client, auth_headers, test_user, db):
        """Test successfully updating a task."""
        from app.models.task import Task
        
        task = Task(title="Original Title", assigned_to_id=test_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.put(
            f"/tasks/{task.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "status": "in_progress",
                "priority": "urgent"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "urgent"

    def test_update_task_status(self, client, auth_headers, test_user, db):
        """Test updating task status."""
        from app.models.task import Task
        
        task = Task(title="Test Task", assigned_to_id=test_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.put(
            f"/tasks/{task.id}",
            headers=auth_headers,
            json={"status": "done"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "done"

    def test_update_task_not_found(self, client, auth_headers):
        """Test updating nonexistent task."""
        response = client.put(
            "/tasks/99999",
            headers=auth_headers,
            json={"title": "New Title"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_not_authorized(self, client, auth_headers, admin_user, db):
        """Test updating task not assigned to user."""
        from app.models.task import Task
        
        task = Task(title="Admin Task", assigned_to_id=admin_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.put(
            f"/tasks/{task.id}",
            headers=auth_headers,
            json={"title": "Hacked Title"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteTask:
    """Test deleting tasks."""

    def test_delete_task_success(self, client, auth_headers, test_user, db):
        """Test successfully deleting a task."""
        from app.models.task import Task
        
        task = Task(title="To Delete", assigned_to_id=test_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id
        
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task_not_found(self, client, auth_headers):
        """Test deleting nonexistent task."""
        response = client.delete("/tasks/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_task_not_authorized(self, client, auth_headers, admin_user, db):
        """Test deleting task not assigned to user."""
        from app.models.task import Task
        
        task = Task(title="Admin Task", assigned_to_id=admin_user.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.delete(f"/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTaskStatuses:
    """Test task status transitions."""

    def test_task_status_pending_to_in_progress(self, client, auth_headers, test_user, db):
        """Test moving task from pending to in_progress."""
        from app.models.task import Task, TaskStatus
        
        task = Task(title="Test Task", assigned_to_id=test_user.id, status=TaskStatus.PENDING)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.put(
            f"/tasks/{task.id}",
            headers=auth_headers,
            json={"status": "in_progress"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "in_progress"

    def test_task_status_in_progress_to_done(self, client, auth_headers, test_user, db):
        """Test completing a task."""
        from app.models.task import Task, TaskStatus
        
        task = Task(title="Test Task", assigned_to_id=test_user.id, status=TaskStatus.IN_PROGRESS)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        response = client.put(
            f"/tasks/{task.id}",
            headers=auth_headers,
            json={"status": "done"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "done"


class TestTaskPriorities:
    """Test task priority levels."""

    def test_create_task_low_priority(self, client, auth_headers):
        """Test creating low priority task."""
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={"title": "Low Priority Task", "priority": "low"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["priority"] == "low"

    def test_create_task_urgent_priority(self, client, auth_headers):
        """Test creating urgent priority task."""
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={"title": "Urgent Task", "priority": "urgent"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["priority"] == "urgent"


class TestTaskDueDates:
    """Test task due date functionality."""

    def test_create_task_with_due_date(self, client, auth_headers):
        """Test creating task with due date."""
        due_date = str(date.today() + timedelta(days=7))
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": "Task with Due Date",
                "due_date": due_date
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["due_date"] == due_date

    def test_filter_tasks_by_due_date(self, client, auth_headers, test_user, db):
        """Test filtering tasks by due date range."""
        from app.models.task import Task
        
        task1 = Task(
            title="Task 1",
            assigned_to_id=test_user.id,
            due_date=date.today() + timedelta(days=5)
        )
        task2 = Task(
            title="Task 2",
            assigned_to_id=test_user.id,
            due_date=date.today() + timedelta(days=15)
        )
        db.add_all([task1, task2])
        db.commit()
        
        # Filter tasks due within 7 days
        due_before = str(date.today() + timedelta(days=7))
        response = client.get(
            f"/tasks/?due_before={due_before}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
